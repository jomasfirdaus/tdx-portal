import time

from django import forms
from django.core.exceptions import ValidationError

from core.i18n import DEFAULT_LANGUAGE, t

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Honeypot field: real users never see or fill this (hidden via CSS).
    # Bots that auto-fill every field will trip it.
    website = forms.CharField(required=False, widget=forms.HiddenInput())
    # Timestamp the form was rendered; reject submissions that come back
    # implausibly fast (a hallmark of scripted spam).
    ts = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "field-input", "maxlength": 150}),
            "email": forms.EmailInput(attrs={"class": "field-input", "maxlength": 254}),
            "phone": forms.TextInput(attrs={"class": "field-input", "maxlength": 30}),
            "subject": forms.TextInput(attrs={"class": "field-input", "maxlength": 200}),
            "message": forms.Textarea(attrs={"class": "field-input", "rows": 5, "maxlength": 3000}),
        }

    def __init__(self, *args, lang=DEFAULT_LANGUAGE, **kwargs):
        """Accepts the active site language so every validation message the
        visitor can see (including Django's built-in required/invalid
        errors) is rendered in English, Tetum, or Portuguese."""
        super().__init__(*args, **kwargs)
        self.lang = lang
        required_msg = t("contact.err_required", lang)
        for field in self.fields.values():
            if field.required:
                field.error_messages["required"] = required_msg
        self.fields["email"].error_messages["invalid"] = t("contact.err_invalid_email", lang)

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise ValidationError(t("contact.err_spam", self.lang))
        return value

    def clean_ts(self):
        value = self.cleaned_data.get("ts")
        try:
            submitted_at = float(value)
        except (TypeError, ValueError):
            return value
        if time.time() - submitted_at < 2:
            raise ValidationError(t("contact.err_too_fast", self.lang))
        return value

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise ValidationError(t("contact.err_message_short", self.lang))
        return message
