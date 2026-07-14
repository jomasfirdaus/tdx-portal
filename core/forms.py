"""
Shared building blocks for public-facing forms.

AntiSpamFormMixin holds the honeypot + timestamp technique that was
originally written inline inside contact.forms.ContactForm. It's extracted
here so appointments.forms.AppointmentForm (and any future public form)
can reuse it instead of copy-pasting. contact/forms.py keeps its own inline
copy for now — deliberately left untouched to avoid touching working code —
and can be migrated onto this mixin later if desired.
"""

import time

from django import forms
from django.core.exceptions import ValidationError

from core.i18n import DEFAULT_LANGUAGE, t


class AntiSpamFormMixin(forms.Form):
    # Honeypot field: real visitors never see or fill this (hidden via CSS
    # in the template). Bots that auto-fill every field will trip it.
    website = forms.CharField(required=False, widget=forms.HiddenInput())
    # Timestamp the form was rendered; reject submissions that come back
    # implausibly fast (a hallmark of scripted spam).
    ts = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            # Reuses contact's translated strings — the message is generic
            # ("Spam detected"), not specific to the contact form.
            raise ValidationError(t("contact.err_spam", getattr(self, "lang", DEFAULT_LANGUAGE)))
        return value

    def clean_ts(self):
        value = self.cleaned_data.get("ts")
        try:
            submitted_at = float(value)
        except (TypeError, ValueError):
            return value
        if time.time() - submitted_at < 2:
            raise ValidationError(t("contact.err_too_fast", getattr(self, "lang", DEFAULT_LANGUAGE)))
        return value
