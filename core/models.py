from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-\(\)]{6,20}$",
    message="Enter a valid phone number.",
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteProfile(TimeStampedModel):
    """
    Singleton table holding the organization's identity, About, Vision &
    Mission, and contact/social details. Enforced to a single row (pk=1) via
    save()/get_solo() so the dashboard always edits the same record.
    """

    org_name = models.CharField(max_length=150, default="Timor Diagnostics (TDx)")
    short_name = models.CharField(max_length=30, default="TDx")
    founded_year = models.PositiveIntegerField(blank=True, null=True)

    tagline_en = models.CharField(max_length=220, blank=True)
    tagline_tet = models.CharField(max_length=220, blank=True)
    tagline_pt = models.CharField(max_length=220, blank=True)

    about_en = models.TextField(blank=True)
    about_tet = models.TextField(blank=True)
    about_pt = models.TextField(blank=True)

    about_secondary_en = models.TextField(blank=True, help_text="Second About paragraph (e.g. bridging public/private gaps).")
    about_secondary_tet = models.TextField(blank=True)
    about_secondary_pt = models.TextField(blank=True)

    vision_en = models.TextField(blank=True)
    vision_tet = models.TextField(blank=True)
    vision_pt = models.TextField(blank=True)

    mission_en = models.TextField(blank=True)
    mission_tet = models.TextField(blank=True)
    mission_pt = models.TextField(blank=True)

    logo = models.ImageField(upload_to="site/", blank=True, null=True)
    favicon = models.ImageField(upload_to="site/", blank=True, null=True)
    hero_image = models.ImageField(upload_to="site/", blank=True, null=True)

    address_en = models.CharField(max_length=255, blank=True)
    address_tet = models.CharField(max_length=255, blank=True)
    address_pt = models.CharField(max_length=255, blank=True)

    phone_primary = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    phone_secondary = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    email_primary = models.EmailField(blank=True)
    map_embed_url = models.URLField(blank=True, help_text="Google Maps embed URL for the Contact page.")

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Site Profile"

    def __str__(self):
        return self.org_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        from django.core.cache import cache
        obj = cache.get("site_profile_singleton")
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set("site_profile_singleton", obj, 300)
        return obj


class ServiceArea(TimeStampedModel):
    """Maps to the 'Services & Expertise' table (Clinical Diagnostics, etc.)."""

    name_en = models.CharField(max_length=120)
    name_tet = models.CharField(max_length=120, blank=True)
    name_pt = models.CharField(max_length=120, blank=True)

    function_en = models.TextField(help_text="Core function")
    function_tet = models.TextField(blank=True)
    function_pt = models.TextField(blank=True)

    value_en = models.TextField(help_text="Strategic value")
    value_tet = models.TextField(blank=True)
    value_pt = models.TextField(blank=True)

    icon = models.CharField(max_length=40, blank=True, help_text="Icon key, e.g. 'microscope', 'shield', 'graduation'.")
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.name_en


class CoreValue(TimeStampedModel):
    name_en = models.CharField(max_length=80)
    name_tet = models.CharField(max_length=80, blank=True)
    name_pt = models.CharField(max_length=80, blank=True)

    description_en = models.TextField(blank=True)
    description_tet = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.name_en


class Statistic(TimeStampedModel):
    """Small counters shown in the homepage 'TDx at a glance' strip."""

    label_en = models.CharField(max_length=80)
    label_tet = models.CharField(max_length=80, blank=True)
    label_pt = models.CharField(max_length=80, blank=True)

    value = models.CharField(max_length=20, help_text="e.g. '3', '24/7', '13'")
    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return f"{self.value} {self.label_en}"
