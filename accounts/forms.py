from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class StaffLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username", "class": "field-input"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "field-input"}),
    )


class StaffSetPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field-input"
