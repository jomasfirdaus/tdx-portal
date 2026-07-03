import time

from django import forms
from django.core.exceptions import ValidationError

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

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise ValidationError("Spam detected.")
        return value

    def clean_ts(self):
        value = self.cleaned_data.get("ts")
        try:
            submitted_at = float(value)
        except (TypeError, ValueError):
            return value
        if time.time() - submitted_at < 2:
            raise ValidationError("Please take a moment to fill in the form.")
        return value

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise ValidationError("Please write a slightly longer message so we can help you.")
        return message
