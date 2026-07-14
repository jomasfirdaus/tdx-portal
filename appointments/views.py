import datetime
import logging
import time

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.i18n import t as translate
from core.models import ServiceArea
from core.translation import tr as translate_field

from .forms import AppointmentForm
from .models import AppointmentRequest, AppointmentSlot, AppointmentStatus

security_logger = logging.getLogger("tdx.security")

# Maps the fixed English messages raised by AppointmentRequest.create_if_available()
# to translated appointment.err_* strings. The model layer's messages stay in
# English by design (it's domain/business logic, not UI) — this mapping is the
# i18n boundary between that layer and the public-facing view.
_CAPACITY_ERROR_KEYS = {
    "This slot is fully booked for the selected date.": "appointment.err_slot_full",
    "This slot is not currently active.": "appointment.err_slot_inactive",
    "The selected date does not fall on this slot's day of week.": "appointment.err_date_mismatch",
    "The selected date has already passed.": "appointment.err_date_past",
}


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _notify_staff(appointment):
    slot = appointment.slot
    send_mail(
        subject=f"[TDx Website] New appointment request: {slot.service_area.name_en}",
        message=(
            f"From: {appointment.full_name} <{appointment.email}>\n"
            f"Phone: {appointment.phone}\n"
            f"Service: {slot.service_area.name_en}\n"
            f"Date: {appointment.appointment_date} "
            f"({slot.get_day_of_week_display()}, {slot.start_time}-{slot.end_time})\n\n"
            f"Notes:\n{appointment.notes or '-'}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.APPOINTMENT_NOTIFY_EMAIL],
        fail_silently=True,
    )


def _notify_requester(appointment):
    slot = appointment.slot
    send_mail(
        subject="Your TDx appointment request has been received",
        message=(
            f"Hi {appointment.full_name},\n\n"
            f"We've received your appointment request for {slot.service_area.name_en} "
            f"on {appointment.appointment_date} ({slot.start_time}-{slot.end_time}).\n"
            "Our team will confirm shortly.\n\nTDx"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appointment.email],
        fail_silently=True,
    )


@require_http_methods(["GET", "POST"])
def appointment_view(request):
    ip = _client_ip(request)
    lang = getattr(request, "LANGUAGE", "en")
    throttle_key = f"appointment_throttle:{ip}"

    if request.method == "POST":
        if cache.get(throttle_key, 0) >= 5:
            messages.error(request, translate("appointment.err_throttled", lang))
            return redirect("appointments:appointment")

        form = AppointmentForm(request.POST, lang=lang)
        if form.is_valid():
            data = form.cleaned_data
            try:
                appointment = AppointmentRequest.create_if_available(
                    slot=data["slot"],
                    appointment_date=data["appointment_date"],
                    location=data.get("location"),
                    full_name=data["full_name"],
                    email=data["email"],
                    phone=data["phone"],
                    notes=data.get("notes", ""),
                    ip_address=ip,
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                )
            except ValidationError as exc:
                # Capacity/availability can only be known authoritatively at
                # the moment of booking (a slot can fill up between page
                # load and submit, even though the form itself was valid).
                # Surface it as a form-level error and fall through to the
                # same re-render path as any other invalid submission.
                for message in exc.messages:
                    key = _CAPACITY_ERROR_KEYS.get(message)
                    form.add_error(None, translate(key, lang) if key else message)
            else:
                cache.set(throttle_key, cache.get(throttle_key, 0) + 1, timeout=600)

                try:
                    _notify_staff(appointment)
                except Exception:
                    security_logger.exception("appointment_staff_email_failed")

                try:
                    _notify_requester(appointment)
                except Exception:
                    security_logger.exception("appointment_confirmation_email_failed")

                messages.success(request, translate("appointment.success", lang))
                return redirect("appointments:appointment")
    else:
        form = AppointmentForm(initial={"ts": time.time()}, lang=lang)

    return render(request, "public/appointments.html", {"form": form})


def _availability_error(code, message, status):
    """Uniform error shape for every failure case in slot_availability_view:
    {"error": "<machine-readable code>", "message": "<localized text>"}."""
    return JsonResponse({"error": code, "message": message}, status=status)


@require_http_methods(["GET"])
def slot_availability_view(request):
    """
    Read-only JSON endpoint: given a ServiceArea id and a calendar date,
    returns the AppointmentSlots that are currently bookable for that
    combination — active, matching the date's day of week, not in the past,
    and with remaining capacity — along with how many openings are left in
    each.

    Plain JsonResponse, no DRF, consistent with the rest of this project.
    Polled by the booking form's Service Area/Date picker — see
    static/js/appointments.js and templates/public/appointments.html.

    GET params:
      - service_area: ServiceArea id (required)
      - date: ISO date, YYYY-MM-DD (required)
    """
    lang = getattr(request, "LANGUAGE", "en")
    service_area_id = request.GET.get("service_area")
    date_param = request.GET.get("date")

    if not service_area_id or not date_param:
        return _availability_error(
            "missing_parameters",
            translate("appointment.err_missing_params", lang),
            400,
        )

    try:
        service_area_id = int(service_area_id)
    except (TypeError, ValueError):
        return _availability_error(
            "invalid_service_area",
            translate("appointment.err_invalid_service_area", lang),
            400,
        )

    try:
        appointment_date = datetime.date.fromisoformat(date_param)
    except (TypeError, ValueError):
        return _availability_error(
            "invalid_date_format",
            translate("appointment.err_invalid_date_format", lang),
            400,
        )

    if appointment_date < timezone.localdate():
        return _availability_error(
            "date_in_past",
            translate("appointment.err_date_past", lang),
            400,
        )

    # Only a service that is active AND explicitly flagged for online
    # booking can be queried — same rule AppointmentForm applies to the
    # slot dropdown, kept consistent here.
    service_area = ServiceArea.objects.filter(
        pk=service_area_id, is_active=True, supports_appointment=True
    ).first()
    if service_area is None:
        return _availability_error(
            "service_area_not_found",
            translate("appointment.err_service_area_not_found", lang),
            404,
        )

    day_of_week = appointment_date.weekday()

    # Annotate the booked count per slot in a single query instead of
    # calling AppointmentRequest.booked_count() per slot (N+1).
    slots = (
        AppointmentSlot.objects.filter(
            service_area=service_area,
            day_of_week=day_of_week,
            is_active=True,
        )
        .annotate(
            booked=Count(
                "appointment_requests",
                filter=Q(appointment_requests__appointment_date=appointment_date)
                & ~Q(appointment_requests__status=AppointmentStatus.CANCELLED),
            )
        )
        .order_by("start_time")
    )

    available_slots = []
    for slot in slots:
        remaining = slot.capacity - slot.booked
        if remaining <= 0:
            continue
        available_slots.append(
            {
                "id": slot.pk,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "capacity": slot.capacity,
                "booked": slot.booked,
                "remaining": remaining,
            }
        )

    return JsonResponse(
        {
            "service_area": {
                # Localized via core.translation.tr() — the project's DB-level
                # i18n mechanism (name_en/name_tet/name_pt) — resolved against
                # request.LANGUAGE, same as templates do with the {% tf %} tag.
                "id": service_area.pk,
                "name": translate_field(service_area, "name", lang),
            },
            "date": appointment_date.isoformat(),
            "day_of_week": day_of_week,
            "slots": available_slots,
        }
    )
