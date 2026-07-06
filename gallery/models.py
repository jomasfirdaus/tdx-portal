from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.models import TimeStampedModel


class Album(TimeStampedModel):
    title_en = models.CharField(max_length=180)
    title_tet = models.CharField(max_length=180, blank=True)
    title_pt = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)

    description_en = models.TextField(blank=True)
    description_tet = models.TextField(blank=True)
    description_pt = models.TextField(blank=True)

    cover_image = models.ImageField(upload_to="gallery/covers/", blank=True, null=True)
    event_date = models.DateField(blank=True, null=True, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-event_date", "-created_at"]
        indexes = [models.Index(fields=["is_published", "-event_date"])]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)[:200]
            slug, i = base, 1
            while Album.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("gallery:detail", kwargs={"slug": self.slug})

    @property
    def photo_count(self):
        return self.photos.count()


class Photo(TimeStampedModel):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="photos", db_index=True)
    image = models.ImageField(upload_to="gallery/photos/")
    caption_en = models.CharField(max_length=200, blank=True)
    caption_tet = models.CharField(max_length=200, blank=True)
    caption_pt = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["album", "order"])]

    def __str__(self):
        # Guard against unsaved/partial instances: templates auto-call
        # callables and repr/str may run before the FK is assigned.
        if self.album_id:
            return f"{self.album.title_en} #{self.pk}"
        return f"Photo #{self.pk or 'new'}"
