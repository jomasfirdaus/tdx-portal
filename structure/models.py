from django.db import models

from core.models import TimeStampedModel


class Department(TimeStampedModel):
    """Org-chart node: Board, Managing Director, Finance Unit, Technical Core, etc."""

    CATEGORY_CHOICES = [
        ("governance", "Governance"),
        ("executive", "Executive"),
        ("unit", "Operational Unit"),
    ]

    name_en = models.CharField(max_length=120)
    name_tet = models.CharField(max_length=120, blank=True)
    name_pt = models.CharField(max_length=120, blank=True)

    description_en = models.TextField(blank=True)
    description_tet = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="unit", db_index=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="children", db_index=True,
    )
    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["is_active", "category", "order"])]

    def __str__(self):
        return self.name_en


class TeamMember(TimeStampedModel):
    full_name = models.CharField(max_length=150, db_index=True)

    role_title_en = models.CharField(max_length=150)
    role_title_tet = models.CharField(max_length=150, blank=True)
    role_title_pt = models.CharField(max_length=150, blank=True)

    bio_en = models.TextField(blank=True)
    bio_tet = models.TextField(blank=True)
    bio_pt = models.TextField(blank=True)

    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="members", db_index=True,
    )
    photo = models.ImageField(upload_to="team/", blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)

    is_board_member = models.BooleanField(default=False, db_index=True)
    is_leadership = models.BooleanField(default=False, db_index=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "full_name"]
        indexes = [
            models.Index(fields=["is_published", "is_board_member", "order"]),
            models.Index(fields=["is_published", "is_leadership", "order"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.role_title_en})"
