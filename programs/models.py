from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import TimeStampedModel


class ProgramCategory(TimeStampedModel):
    name_en = models.CharField(max_length=100)
    name_tet = models.CharField(max_length=100, blank=True)
    name_pt = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(max_length=110, unique=True, db_index=True)

    class Meta:
        verbose_name_plural = "Program categories"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)


class PublishedProgramManager(models.Manager):
    def get_queryset(self):
        # select_related avoids an N+1 query for `category` on every list/detail view.
        return super().get_queryset().select_related("category").filter(is_published=True)


class Program(TimeStampedModel):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
    ]

    title_en = models.CharField(max_length=200)
    title_tet = models.CharField(max_length=200, blank=True)
    title_pt = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    summary_en = models.CharField(max_length=300, blank=True)
    summary_tet = models.CharField(max_length=300, blank=True)
    summary_pt = models.CharField(max_length=300, blank=True)

    description_en = models.TextField(blank=True)
    description_tet = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    category = models.ForeignKey(
        ProgramCategory, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="programs", db_index=True,
    )
    cover_image = models.ImageField(upload_to="programs/", blank=True, null=True)
    location = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ongoing", db_index=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    is_featured = models.BooleanField(default=False, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)

    objects = models.Manager()
    published = PublishedProgramManager()

    class Meta:
        ordering = ["-is_featured", "-start_date", "-created_at"]
        indexes = [
            models.Index(fields=["is_published", "is_featured", "-start_date"]),
            models.Index(fields=["is_published", "status"]),
        ]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)[:200]
            slug, i = base, 1
            while Program.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("programs:detail", kwargs={"slug": self.slug})
