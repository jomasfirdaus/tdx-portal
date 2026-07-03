import os

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import AdminUser
from core.models import CoreValue, ServiceArea, SiteProfile, Statistic
from gallery.models import Album, Photo
from news.models import NewsCategory, NewsPost
from programs.models import Program, ProgramCategory
from structure.models import Department, TeamMember

FIELD_WIDGET = forms.TextInput(attrs={"class": "field-input"})
TEXTAREA_WIDGET = forms.Textarea(attrs={"class": "field-input", "rows": 4})


def validate_image_file(f):
    """Defense in depth beyond ImageField's own validation: whitelist
    extensions and cap size, so a renamed executable or an oversized upload
    can't reach disk even from a trusted staff account."""
    if f is None:
        return
    ext = os.path.splitext(f.name)[1].lower()
    from django.conf import settings
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}")
    max_bytes = settings.MAX_IMAGE_UPLOAD_MB * 1024 * 1024
    if f.size > max_bytes:
        raise ValidationError(f"File too large. Maximum size is {settings.MAX_IMAGE_UPLOAD_MB} MB.")


class ImageValidationMixin(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ImageField):
                validate_image_file(cleaned.get(field_name))
        return cleaned


class SiteProfileForm(ImageValidationMixin):
    class Meta:
        model = SiteProfile
        exclude = ["created_at", "updated_at"]
        widgets = {
            "about_en": TEXTAREA_WIDGET, "about_tet": TEXTAREA_WIDGET, "about_pt": TEXTAREA_WIDGET,
            "about_secondary_en": TEXTAREA_WIDGET, "about_secondary_tet": TEXTAREA_WIDGET, "about_secondary_pt": TEXTAREA_WIDGET,
            "vision_en": TEXTAREA_WIDGET, "vision_tet": TEXTAREA_WIDGET, "vision_pt": TEXTAREA_WIDGET,
            "mission_en": TEXTAREA_WIDGET, "mission_tet": TEXTAREA_WIDGET, "mission_pt": TEXTAREA_WIDGET,
        }


class ServiceAreaForm(ImageValidationMixin):
    class Meta:
        model = ServiceArea
        exclude = ["created_at", "updated_at"]
        widgets = {
            "function_en": TEXTAREA_WIDGET, "function_tet": TEXTAREA_WIDGET, "function_pt": TEXTAREA_WIDGET,
            "value_en": TEXTAREA_WIDGET, "value_tet": TEXTAREA_WIDGET, "value_pt": TEXTAREA_WIDGET,
        }


class CoreValueForm(ImageValidationMixin):
    class Meta:
        model = CoreValue
        exclude = ["created_at", "updated_at"]
        widgets = {
            "description_en": TEXTAREA_WIDGET, "description_tet": TEXTAREA_WIDGET, "description_pt": TEXTAREA_WIDGET,
        }


class StatisticForm(ImageValidationMixin):
    class Meta:
        model = Statistic
        exclude = ["created_at", "updated_at"]


class DepartmentForm(ImageValidationMixin):
    class Meta:
        model = Department
        exclude = ["created_at", "updated_at"]
        widgets = {
            "description_en": TEXTAREA_WIDGET, "description_tet": TEXTAREA_WIDGET, "description_pt": TEXTAREA_WIDGET,
        }


class TeamMemberForm(ImageValidationMixin):
    class Meta:
        model = TeamMember
        exclude = ["created_at", "updated_at"]
        widgets = {
            "bio_en": TEXTAREA_WIDGET, "bio_tet": TEXTAREA_WIDGET, "bio_pt": TEXTAREA_WIDGET,
        }


class ProgramCategoryForm(forms.ModelForm):
    class Meta:
        model = ProgramCategory
        exclude = ["created_at", "updated_at", "slug"]


class ProgramForm(ImageValidationMixin):
    class Meta:
        model = Program
        exclude = ["created_at", "updated_at", "slug"]
        widgets = {
            "summary_en": TEXTAREA_WIDGET, "summary_tet": TEXTAREA_WIDGET, "summary_pt": TEXTAREA_WIDGET,
            "description_en": forms.Textarea(attrs={"class": "field-input", "rows": 8}),
            "description_tet": forms.Textarea(attrs={"class": "field-input", "rows": 8}),
            "description_pt": forms.Textarea(attrs={"class": "field-input", "rows": 8}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "field-input"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "field-input"}),
        }


class NewsCategoryForm(forms.ModelForm):
    class Meta:
        model = NewsCategory
        exclude = ["created_at", "updated_at", "slug"]


class NewsPostForm(ImageValidationMixin):
    class Meta:
        model = NewsPost
        exclude = ["created_at", "updated_at", "slug", "author", "views_count"]
        widgets = {
            "excerpt_en": TEXTAREA_WIDGET, "excerpt_tet": TEXTAREA_WIDGET, "excerpt_pt": TEXTAREA_WIDGET,
            "content_en": forms.Textarea(attrs={"class": "field-input rich", "rows": 12}),
            "content_tet": forms.Textarea(attrs={"class": "field-input rich", "rows": 12}),
            "content_pt": forms.Textarea(attrs={"class": "field-input rich", "rows": 12}),
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "field-input"}),
        }


class AlbumForm(ImageValidationMixin):
    class Meta:
        model = Album
        exclude = ["created_at", "updated_at", "slug"]
        widgets = {
            "description_en": TEXTAREA_WIDGET, "description_tet": TEXTAREA_WIDGET, "description_pt": TEXTAREA_WIDGET,
            "event_date": forms.DateInput(attrs={"type": "date", "class": "field-input"}),
        }


class PhotoForm(ImageValidationMixin):
    class Meta:
        model = Photo
        exclude = ["created_at", "updated_at"]


class AdminUserForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"class": "field-input"}), required=False)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={"class": "field-input"}), required=False)

    class Meta:
        model = AdminUser
        fields = ["username", "first_name", "last_name", "email", "phone", "role", "is_active"]
        widgets = {
            "username": FIELD_WIDGET, "first_name": FIELD_WIDGET, "last_name": FIELD_WIDGET,
            "email": FIELD_WIDGET, "phone": FIELD_WIDGET,
        }

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match.")
            from django.contrib.auth.password_validation import validate_password
            validate_password(p1)
        elif not self.instance.pk:
            raise ValidationError("A password is required for new accounts.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
