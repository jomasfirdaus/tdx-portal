from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.forms import AntiSpamFormMixin
from core.i18n import DEFAULT_LANGUAGE, t
from core.models import ServiceArea
from core.translation import tr as translate_field

from .models import AppointmentRequest, AppointmentSlot


class AppointmentForm(AntiSpamFormMixin, forms.ModelForm):
    # Not a model field on AppointmentRequest (the model only stores `slot`,
    # which already implies its service_area). Declared here purely to drive
    # the public page's Service Area -> Date -> Slot picker: the frontend
    # queries appointments:availability with this value, then populates the
    # `slot` choices from the response. Ignored by ModelForm when saving
    # (only Meta.fields map onto the instance), but still validated below so
    # a slot/service_area mismatch is rejected even with JS disabled/bypassed.
    service_area = forms.ModelChoiceField(
        queryset=ServiceArea.objects.filter(is_active=True, supports_appointment=True),
        required=True,
    )

    class Meta:
        model = AppointmentRequest
        fields = ["slot", "location", "appointment_date", "full_name", "email", "phone", "notes"]
        widgets = {
            "appointment_date": forms.DateInput(attrs={"class": "field-input", "type": "date"}),
            "full_name": forms.TextInput(attrs={"class": "field-input", "maxlength": 150}),
            "email": forms.EmailInput(attrs={"class": "field-input", "maxlength": 254}),
            "phone": forms.TextInput(attrs={"class": "field-input", "maxlength": 30}),
            "notes": forms.Textarea(attrs={"class": "field-input", "rows": 4, "maxlength": 2000}),
        }

    def __init__(self, *args, lang=DEFAULT_LANGUAGE, **kwargs):
        """Accepts the active site language so every validation message the
        visitor can see is rendered in English, Tetum, or Portuguese —
        mirrors ContactForm.__init__."""
        super().__init__(*args, **kwargs)
        self.lang = lang

        required_msg = t("appointment.err_required", lang)
        for field in self.fields.values():
            if field.required:
                field.error_messages["required"] = required_msg
        self.fields["email"].error_messages["invalid"] = t("appointment.err_invalid_email", lang)

        # Only bookable slots are offered: active, and belonging to a
        # ServiceArea that is itself active and flagged for online booking.
        # This is a form-level restriction (defense at the edge); the
        # authoritative check still happens again in
        # AppointmentRequest.create_if_available() at submission time.
        self.fields["slot"].queryset = (
            AppointmentSlot.objects.filter(
                is_active=True,
                service_area__is_active=True,
                service_area__supports_appointment=True,
            )
            .select_related("service_area")
        )
        self.fields["slot"].label_from_instance = lambda slot: (
            f"{translate_field(slot.service_area, 'name', lang)} — "
            f"{slot.get_day_of_week_display()} {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        )
        self.fields["location"].required = False
        self.fields["service_area"].label_from_instance = lambda obj: translate_field(obj, "name", lang)
        self.fields["appointment_date"].widget.attrs["min"] = timezone.localdate().isoformat()
        self.fields["slot"].widget.attrs["aria-describedby"] = "slot-hint"

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        if appointment_date and appointment_date < timezone.localdate():
            raise ValidationError(t("appointment.err_date_past", self.lang))
        return appointment_date

    def clean(self):
        cleaned = super().clean()
        slot = cleaned.get("slot")
        service_area = cleaned.get("service_area")
        # Defense against a bypassed/disabled-JS submission: the picker is
        # supposed to only ever offer slots belonging to the chosen service,
        # but nothing stops a direct POST from pairing them up wrong.
        if slot and service_area and slot.service_area_id != service_area.id:
            self.add_error("slot", t("appointment.err_service_area_mismatch", self.lang))
        return cleaned

    # Note: appointment_date-vs-slot.day_of_week cross-field validation is
    # NOT duplicated here — ModelForm._post_clean() already calls
    # AppointmentRequest.clean() (via instance.full_clean()), which enforces
    # that rule. Slot capacity is deliberately NOT checked here either: it
    # can only be verified atomically at the moment of booking (see
    # AppointmentRequest.create_if_available()), since it can change between
    # page load and submit — the view handles that failure case.
