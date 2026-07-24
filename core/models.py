from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-\(\)]{6,20}$",
    message="Enter a valid phone number.",
)

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Enter a hex color, e.g. #6D28D9.",
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

    address_en = models.CharField(max_length=255, blank=True)
    address_tet = models.CharField(max_length=255, blank=True)
    address_pt = models.CharField(max_length=255, blank=True)

    phone_primary = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    phone_secondary = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    email_primary = models.EmailField(blank=True)
    map_embed_url = models.URLField(blank=True, help_text="Legacy Google Maps embed URL — superseded by the Locations module (Dashboard → Locations).")

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


class Location(TimeStampedModel):
    """
    A physical office/branch shown on the website (homepage + contact page)
    with an interactive Leaflet/OpenStreetMap map. Multiple rows are allowed
    so the module stays reusable if TDx opens additional branches; the row
    flagged `is_primary` (or the first active one) is treated as the main
    office.
    """

    name_en = models.CharField(max_length=150)
    name_tet = models.CharField(max_length=150, blank=True)
    name_pt = models.CharField(max_length=150, blank=True)

    address_en = models.CharField(max_length=255, blank=True)
    address_tet = models.CharField(max_length=255, blank=True)
    address_pt = models.CharField(max_length=255, blank=True)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="e.g. -8.556856. Leave blank for a non-physical option (e.g. Home Collection).",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="e.g. 125.560314. Leave blank for a non-physical option (e.g. Home Collection).",
    )
    google_maps_url = models.URLField(
        blank=True,
        help_text="Optional 'Get Directions' link. If empty, a directions link is built from the coordinates.",
    )

    phone = models.CharField(max_length=30, blank=True, validators=[phone_validator])
    email = models.EmailField(blank=True)

    opening_hours_en = models.TextField(blank=True, help_text="One line per entry, e.g. 'Mon–Fri: 08:00–17:00'.")
    opening_hours_tet = models.TextField(blank=True)
    opening_hours_pt = models.TextField(blank=True)

    is_primary = models.BooleanField(default=False, db_index=True, help_text="Main office highlighted first.")
    show_on_map = models.BooleanField(
        default=True, db_index=True,
        help_text="Show on the homepage/contact page map. Uncheck for non-physical options "
        "(e.g. Home Collection) that should still be selectable when booking an appointment.",
    )
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-is_primary", "order", "id"]
        indexes = [models.Index(fields=["is_active", "-is_primary", "order"])]

    def __str__(self):
        return self.name_en

    @property
    def directions_url(self):
        """External directions link: admin-supplied URL wins, otherwise an
        OpenStreetMap directions link built from the stored coordinates (no
        API key required). Returns "" when neither is available (e.g. a
        non-physical option like Home Collection)."""
        if self.google_maps_url:
            return self.google_maps_url
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.openstreetmap.org/directions?to={self.latitude}%2C{self.longitude}"
        return ""


class PageKey(models.TextChoices):
    """Every public page a PageHeader row can be attached to. Adding a new
    public page means adding a value here (and seeding a row for it) —
    nothing about the header content itself is hardcoded per page."""

    HOME = "home", "Home"
    PROFILE = "profile", "Profile"
    VISION_MISSION = "vision_mission", "Vision & Mission"
    PROGRAMS = "programs", "Programs"
    STRUCTURE = "structure", "Team & Structure"
    NEWS = "news", "News"
    GALLERY = "gallery", "Gallery"
    CONTACT = "contact", "Contact"
    APPOINTMENTS = "appointments", "Book Appointment"


class HeaderHeight(models.TextChoices):
    SMALL = "sm", "Small (~240px)"
    MEDIUM = "md", "Medium (~360px)"
    LARGE = "lg", "Large (~480px)"
    FULL = "full", "Full screen"


class PageHeader(TimeStampedModel):
    """
    Admin-configurable banner shown at the top of every public page (one row
    per PageKey), rendered through the shared {% page_header %} tag /
    partials/page_header.html so no page hardcodes its own title, background,
    or colors. An inactive or missing row falls back to a plain default
    banner — a page never renders broken because its header hasn't been
    configured yet.

    background_image fills the decorative panel on the right when set
    (Dashboard -> Page Headers); when it's empty, the panel falls back to
    the same purple-to-green look recreated in CSS/SVG
    (partials/page_header_art.html), so a page never renders with a blank
    header. "home"'s row ships with a seeded default image (see seed_tdx)
    reproducing that same fallback look, so Home's approved appearance is
    unchanged out of the box while still being a real, admin-editable image.
    """

    page_key = models.CharField(max_length=30, choices=PageKey.choices, unique=True, db_index=True)

    title_en = models.CharField(max_length=200, blank=True)
    title_tet = models.CharField(max_length=200, blank=True)
    title_pt = models.CharField(max_length=200, blank=True)

    subtitle_en = models.CharField(max_length=300, blank=True)
    subtitle_tet = models.CharField(max_length=300, blank=True)
    subtitle_pt = models.CharField(max_length=300, blank=True)

    motto_en = models.CharField(max_length=150, blank=True, help_text="Short italic line under the title, e.g. 'Saúde diak, ba moris diak'.")
    motto_tet = models.CharField(max_length=150, blank=True)
    motto_pt = models.CharField(max_length=150, blank=True)

    tagline_en = models.CharField(max_length=150, blank=True, help_text="Smaller line under the motto, e.g. 'Good health for a good life'.")
    tagline_tet = models.CharField(max_length=150, blank=True)
    tagline_pt = models.CharField(max_length=150, blank=True)

    background_image = models.ImageField(upload_to="page_headers/", blank=True, null=True)
    logo = models.ImageField(
        upload_to="page_headers/logos/", blank=True, null=True,
        help_text="Optional watermark/logo shown within the header banner.",
    )

    overlay_color = models.CharField(
        max_length=7, blank=True, default="#2E1065", validators=[hex_color_validator],
        help_text="Tints the decorative background panel. Leave blank to use the default purple-to-green look.",
    )
    overlay_opacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0-100. Intensity of the decorative background panel.",
    )
    text_color = models.CharField(
        max_length=7, blank=True, default="", validators=[hex_color_validator],
        help_text="Overrides the title/breadcrumb color. Leave blank to use the theme default.",
    )
    height = models.CharField(max_length=6, choices=HeaderHeight.choices, default=HeaderHeight.MEDIUM)

    show_breadcrumb = models.BooleanField(default=True)
    is_active = models.BooleanField(
        default=True, db_index=True,
        help_text="When off, the page falls back to a plain default header.",
    )

    class Meta:
        verbose_name = "Page Header"
        ordering = ["page_key"]

    def __str__(self):
        return self.get_page_key_display()

    @property
    def overlay_opacity_ratio(self):
        return self.overlay_opacity / 100

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete(f"page_header:{self.page_key}")

    @classmethod
    def get_for_page(cls, page_key):
        from django.core.cache import cache
        cache_key = f"page_header:{page_key}"
        header = cache.get(cache_key)
        if header is None:
            header = cls.objects.filter(page_key=page_key).first()
            cache.set(cache_key, header if header is not None else False, 300)
            return header
        return header or None


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

    supports_appointment = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If enabled, this service can be booked online through the Appointment module.",
    )

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
