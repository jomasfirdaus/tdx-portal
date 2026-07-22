"""
Unit tests for the appointments app's database layer only.

Scope: AppointmentSlot (overlap validation, activation toggling,
day_of_week handling) and AppointmentRequest (booking creation, default
status, date-vs-day_of_week validation, and capacity enforcement via
AppointmentRequest.create_if_available()). No views, forms, or dashboard
wiring exist yet — those are covered separately once the controller layer
is implemented.
"""

import datetime
import threading

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from appointments.forms import AppointmentForm
from appointments.models import (
    AppointmentRequest,
    AppointmentSlot,
    AppointmentStatus,
    DayOfWeek,
)
from core.models import Location, ServiceArea


def make_service_area(**overrides):
    fields = dict(
        name_en="Panel Test",
        function_en="Routine panel testing",
        value_en="Early detection of common conditions",
    )
    fields.update(overrides)
    return ServiceArea.objects.create(**fields)


def next_weekday(weekday):
    """Returns the next real calendar date (strictly after today) that
    falls on the given DayOfWeek value, so appointment_date/day_of_week
    comparisons in tests use dates that actually exist on the calendar."""
    today = timezone.localdate()
    days_ahead = (weekday - today.weekday()) % 7
    days_ahead = days_ahead or 7
    return today + datetime.timedelta(days=days_ahead)


class AppointmentSlotTests(TestCase):
    def setUp(self):
        self.service_area = make_service_area()

    def test_create_valid_slot(self):
        slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=5,
        )
        self.assertTrue(slot.is_active)
        self.assertEqual(slot.capacity, 5)

    def test_end_time_before_start_time_rejected(self):
        with self.assertRaises(ValidationError):
            AppointmentSlot.objects.create(
                service_area=self.service_area,
                day_of_week=DayOfWeek.MONDAY,
                start_time=datetime.time(10, 0),
                end_time=datetime.time(9, 0),
            )

    def test_end_time_equal_start_time_rejected(self):
        with self.assertRaises(ValidationError):
            AppointmentSlot.objects.create(
                service_area=self.service_area,
                day_of_week=DayOfWeek.MONDAY,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(9, 0),
            )

    def test_overlapping_slot_same_service_area_same_day_rejected(self):
        AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        with self.assertRaises(ValidationError):
            AppointmentSlot.objects.create(
                service_area=self.service_area,
                day_of_week=DayOfWeek.MONDAY,
                start_time=datetime.time(9, 30),
                end_time=datetime.time(10, 30),
            )

    def test_slot_fully_contained_in_existing_slot_rejected(self):
        AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(12, 0),
        )
        with self.assertRaises(ValidationError):
            AppointmentSlot.objects.create(
                service_area=self.service_area,
                day_of_week=DayOfWeek.MONDAY,
                start_time=datetime.time(10, 0),
                end_time=datetime.time(11, 0),
            )

    def test_adjacent_touching_slots_are_not_treated_as_overlap(self):
        AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        # 10:00-11:00 starts exactly where the previous slot ends — allowed.
        slot2 = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
        )
        self.assertIsNotNone(slot2.pk)

    def test_same_time_different_day_of_week_allowed(self):
        AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        slot2 = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.TUESDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        self.assertIsNotNone(slot2.pk)

    def test_same_time_different_service_area_allowed(self):
        other_area = make_service_area(name_en="Clinical Diagnostics")
        AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        slot2 = AppointmentSlot.objects.create(
            service_area=other_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        self.assertIsNotNone(slot2.pk)

    def test_editing_existing_slot_does_not_flag_overlap_against_itself(self):
        slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=1,
        )
        slot.capacity = 10
        slot.save()  # must not raise — own pk should be excluded from the overlap check
        slot.refresh_from_db()
        self.assertEqual(slot.capacity, 10)

    def test_invalid_day_of_week_value_rejected(self):
        with self.assertRaises(ValidationError):
            AppointmentSlot.objects.create(
                service_area=self.service_area,
                day_of_week=9,  # not a valid DayOfWeek choice (0-6)
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
            )

    def test_deactivating_slot(self):
        slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        slot.is_active = False
        slot.save()
        slot.refresh_from_db()
        self.assertFalse(slot.is_active)

    def test_reactivating_slot(self):
        slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            is_active=False,
        )
        slot.is_active = True
        slot.save()
        slot.refresh_from_db()
        self.assertTrue(slot.is_active)

    def test_str_representation(self):
        slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        self.assertIn("Panel Test", str(slot))
        self.assertIn("Monday", str(slot))


class AppointmentRequestTests(TestCase):
    def setUp(self):
        self.service_area = make_service_area()
        self.location = Location.objects.create(
            name_en="Dili Main Office",
            address_en="Dili, Timor-Leste",
            latitude=-8.556856,
            longitude=125.560314,
        )
        self.slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=2,
        )
        self.monday = next_weekday(DayOfWeek.MONDAY)
        self.tuesday = next_weekday(DayOfWeek.TUESDAY)

    def _valid_fields(self, **overrides):
        fields = dict(
            slot=self.slot,
            appointment_date=self.monday,
            full_name="Maria Soares",
            email="maria@example.com",
            phone="+670 7723 1234",
        )
        fields.update(overrides)
        return fields

    def test_default_status_is_pending(self):
        appointment = AppointmentRequest.objects.create(**self._valid_fields())
        self.assertEqual(appointment.status, AppointmentStatus.PENDING)

    def test_date_matching_slot_day_of_week_is_valid(self):
        appointment = AppointmentRequest(**self._valid_fields())
        appointment.full_clean()  # should not raise

    def test_date_not_matching_slot_day_of_week_rejected(self):
        appointment = AppointmentRequest(**self._valid_fields(appointment_date=self.tuesday))
        with self.assertRaises(ValidationError):
            appointment.full_clean()

    def test_location_is_optional(self):
        appointment = AppointmentRequest.objects.create(**self._valid_fields())
        self.assertIsNone(appointment.location)

    def test_location_can_be_attached(self):
        appointment = AppointmentRequest.objects.create(**self._valid_fields(location=self.location))
        self.assertEqual(appointment.location, self.location)

    def test_deleting_slot_in_use_is_protected(self):
        AppointmentRequest.objects.create(**self._valid_fields())
        with self.assertRaises(ProtectedError):
            self.slot.delete()

    def test_str_representation(self):
        appointment = AppointmentRequest.objects.create(**self._valid_fields())
        self.assertIn("Maria Soares", str(appointment))


class AppointmentBookingCapacityTests(TestCase):
    """Covers AppointmentRequest.create_if_available() — the single entry
    point booking creation should go through once views exist."""

    def setUp(self):
        self.service_area = make_service_area()
        self.slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=2,
        )
        self.monday = next_weekday(DayOfWeek.MONDAY)

    def _book(self, appointment_date=None, **overrides):
        fields = dict(
            full_name="Maria Soares",
            email="maria@example.com",
            phone="+670 7723 1234",
        )
        fields.update(overrides)
        return AppointmentRequest.create_if_available(
            slot=self.slot,
            appointment_date=appointment_date or self.monday,
            **fields,
        )

    def test_booking_within_capacity_succeeds(self):
        appointment = self._book()
        self.assertEqual(AppointmentRequest.objects.count(), 1)
        self.assertEqual(appointment.status, AppointmentStatus.PENDING)

    def test_booking_without_email_succeeds(self):
        appointment = self._book(email="")
        self.assertEqual(AppointmentRequest.objects.count(), 1)
        self.assertEqual(appointment.email, "")

    def test_booking_up_to_capacity_succeeds(self):
        self._book(email="a@example.com")
        self._book(email="b@example.com")
        self.assertEqual(AppointmentRequest.objects.count(), 2)

    def test_booking_beyond_capacity_rejected(self):
        self._book(email="a@example.com")
        self._book(email="b@example.com")
        with self.assertRaises(ValidationError):
            self._book(email="c@example.com")
        # The rejected attempt must not leave a phantom row behind.
        self.assertEqual(AppointmentRequest.objects.count(), 2)

    def test_cancelled_booking_frees_up_capacity(self):
        self._book(email="a@example.com")
        second = self._book(email="b@example.com")
        second.status = AppointmentStatus.CANCELLED
        second.save()

        third = self._book(email="c@example.com")

        self.assertEqual(third.status, AppointmentStatus.PENDING)
        self.assertEqual(
            AppointmentRequest.objects.exclude(status=AppointmentStatus.CANCELLED).count(),
            2,
        )

    def test_inactive_slot_cannot_be_booked(self):
        self.slot.is_active = False
        self.slot.save()
        with self.assertRaises(ValidationError):
            self._book()
        self.assertEqual(AppointmentRequest.objects.count(), 0)

    def test_date_mismatched_with_slot_day_of_week_rejected(self):
        wrong_date = next_weekday(DayOfWeek.TUESDAY)
        with self.assertRaises(ValidationError):
            self._book(appointment_date=wrong_date)
        self.assertEqual(AppointmentRequest.objects.count(), 0)

    def test_past_date_rejected(self):
        # Regression test: create_if_available() originally only checked
        # day-of-week and capacity — a past date matching the slot's weekday
        # (e.g. last Monday) could slip through even though AppointmentForm
        # separately rejected it. Found during the final engineering review.
        past_monday = self.monday - datetime.timedelta(days=14)
        with self.assertRaises(ValidationError):
            self._book(appointment_date=past_monday)
        self.assertEqual(AppointmentRequest.objects.count(), 0)

    def test_different_dates_have_independent_capacity(self):
        self._book(email="a@example.com")
        self._book(email="b@example.com")  # slot is now full for self.monday

        other_monday = self.monday + datetime.timedelta(days=7)
        appointment = self._book(appointment_date=other_monday, email="c@example.com")

        self.assertIsNotNone(appointment.pk)
        self.assertEqual(AppointmentRequest.objects.count(), 3)


class AppointmentBookingRaceConditionTests(TransactionTestCase):
    """
    Uses TransactionTestCase (real commits, unlike TestCase which wraps
    each test in a transaction that's rolled back) plus real OS threads
    with their own DB connections, so create_if_available()'s
    select_for_update() lock is genuinely exercised under concurrency —
    this is the exact scenario the capacity check exists to prevent.

    Requires a database backend with real row-level locking (MySQL/InnoDB,
    as used by this project). On backends without row locking this test
    may not be meaningful.
    """

    def setUp(self):
        self.service_area = ServiceArea.objects.create(
            name_en="Panel Test",
            function_en="Routine panel testing",
            value_en="Early detection of common conditions",
        )
        self.slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=1,  # a single opening — the classic overbooking scenario
        )
        self.monday = next_weekday(DayOfWeek.MONDAY)

    def test_concurrent_bookings_for_the_last_opening_do_not_overbook(self):
        results = []

        def attempt_booking(email):
            try:
                AppointmentRequest.create_if_available(
                    slot=self.slot,
                    appointment_date=self.monday,
                    full_name="Concurrent Patient",
                    email=email,
                    phone="+670 7723 0000",
                )
                results.append("success")
            except ValidationError:
                results.append("rejected")
            finally:
                connection.close()  # each thread must use its own DB connection

        threads = [
            threading.Thread(target=attempt_booking, args=(f"patient{i}@example.com",))
            for i in range(5)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("rejected"), 4)
        self.assertEqual(
            AppointmentRequest.objects.filter(slot=self.slot, appointment_date=self.monday)
            .exclude(status=AppointmentStatus.CANCELLED)
            .count(),
            1,
        )


class AppointmentFormTests(TestCase):
    """Covers AppointmentForm's own required/optional field rules — the
    layer that decides what the public booking page enforces before a
    submission ever reaches AppointmentRequest.create_if_available()."""

    def setUp(self):
        # supports_appointment must be explicit — it defaults to False, and
        # AppointmentForm.__init__ filters both the slot and service_area
        # querysets down to bookable service areas only.
        self.service_area = make_service_area(supports_appointment=True)
        self.slot = AppointmentSlot.objects.create(
            service_area=self.service_area,
            day_of_week=DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            capacity=2,
        )
        self.monday = next_weekday(DayOfWeek.MONDAY)

    def _form_data(self, **overrides):
        data = dict(
            service_area=self.service_area.pk,
            slot=self.slot.pk,
            appointment_date=self.monday.isoformat(),
            full_name="Maria Soares",
            email="maria@example.com",
            phone="+670 7723 1234",
        )
        data.update(overrides)
        return AppointmentForm(data)

    def test_email_is_not_required(self):
        form = self._form_data(email="")
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_format_still_rejected(self):
        form = self._form_data(email="not-an-email")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
