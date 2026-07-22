from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from core.models import TimeStampedModel, phone_validator


class DayOfWeek(models.IntegerChoices):
    """Mirrors Python's date.weekday() numbering (Monday=0 .. Sunday=6) so
    AppointmentRequest.clean() can compare appointment_date.weekday() to
    slot.day_of_week without a lookup table."""

    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class AppointmentSlot(TimeStampedModel):
    """
    A recurring weekly time slot that a ServiceArea can be booked under
    (e.g. "Panel Test — every Monday, 09:00-10:00, capacity 5"). Deliberately
    NOT tied to a specific calendar date: availability for a given date is
    computed on demand from AppointmentRequest rows, so no background job is
    needed to pre-generate future slots.

    Reusability: because service_area is a plain FK to core.ServiceArea,
    enabling online appointments for a service other than "Panel Test" later
    only requires creating AppointmentSlot rows for that ServiceArea — no
    model or code changes.
    """

    service_area = models.ForeignKey(
        "core.ServiceArea",
        on_delete=models.CASCADE,
        related_name="appointment_slots",
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveSmallIntegerField(
        default=1,
        help_text="Maximum number of bookings allowed for this slot on a single date.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive slots are hidden from booking but keep their history.",
    )

    class Meta:
        ordering = ["service_area", "day_of_week", "start_time"]
        indexes = [
            models.Index(
                fields=["service_area", "day_of_week", "is_active"],
                name="appt_slot_area_day_active_idx",
            ),
        ]
        verbose_name = "Appointment Slot"

    def __str__(self):
        return f"{self.service_area.name_en} — {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self):
        super().clean()

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be after start time."})

        if self.service_area_id is not None and self.start_time and self.end_time:
            overlapping = AppointmentSlot.objects.filter(
                service_area_id=self.service_area_id,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    "This slot overlaps with an existing slot for the same "
                    "service area and day of week."
                )

    def save(self, *args, **kwargs):
        # Enforced here (not only in forms) so the overlap rule holds no
        # matter which caller creates/edits a slot — dashboard CRUD, a
        # management command, or the Django shell.
        self.full_clean()
        super().save(*args, **kwargs)


class AppointmentRequest(TimeStampedModel):
    """A patient's booking against one concrete date of an AppointmentSlot."""

    slot = models.ForeignKey(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name="appointment_requests",
        help_text="Historical bookings must not lose their slot reference, so slots in use cannot be deleted.",
    )
    location = models.ForeignKey(
        "core.Location",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointment_requests",
    )
    appointment_date = models.DateField()

    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, validators=[phone_validator])
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-appointment_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["slot", "appointment_date", "status"],
                name="appt_req_slot_date_status_idx",
            ),
        ]
        verbose_name = "Appointment Request"

    def __str__(self):
        return f"{self.full_name} — {self.slot} on {self.appointment_date}"

    def clean(self):
        super().clean()
        if self.slot_id and self.appointment_date:
            if self.appointment_date.weekday() != self.slot.day_of_week:
                raise ValidationError(
                    {"appointment_date": "The selected date does not fall on this slot's day of week."}
                )

    @classmethod
    def booked_count(cls, slot, appointment_date):
        """Active (non-cancelled) bookings already made for this slot/date."""
        return (
            cls.objects.filter(slot=slot, appointment_date=appointment_date)
            .exclude(status=AppointmentStatus.CANCELLED)
            .count()
        )

    @classmethod
    def create_if_available(cls, *, slot, appointment_date, **fields):
        """
        Atomically validate and create a booking.

        Locks the AppointmentSlot row itself (not the AppointmentRequest
        rows, which may not exist yet for a fresh slot/date) for the
        duration of the transaction, so two concurrent requests for the
        last opening cannot both pass the capacity check. This is the
        single entry point future views/commands should call to create a
        booking — the capacity/availability rule lives here once, not
        duplicated per caller.
        """
        with transaction.atomic():
            locked_slot = (
                AppointmentSlot.objects.select_for_update()
                .select_related("service_area")
                .get(pk=slot.pk)
            )

            if not locked_slot.is_active:
                raise ValidationError("This slot is not currently active.")

            if appointment_date.weekday() != locked_slot.day_of_week:
                raise ValidationError("The selected date does not fall on this slot's day of week.")

            # Was previously only enforced in AppointmentForm.clean_appointment_date(),
            # not here — meaning a direct call to this "single entry point" (e.g. a
            # future admin script or API) could still create a past-dated booking.
            if appointment_date < timezone.localdate():
                raise ValidationError("The selected date has already passed.")

            booked = cls.booked_count(locked_slot, appointment_date)
            if booked >= locked_slot.capacity:
                raise ValidationError("This slot is fully booked for the selected date.")

            appointment = cls(slot=locked_slot, appointment_date=appointment_date, **fields)
            appointment.full_clean()
            appointment.save()
            return appointment
