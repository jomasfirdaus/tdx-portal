import bleach
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from core.models import TimeStampedModel

# Only a conservative subset of HTML is allowed through news body content —
# this blocks stored-XSS via <script>, event handler attributes, etc. even
# though the field is only editable by authenticated staff.
ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "ul", "ol", "li", "a", "h2", "h3", "blockquote", "img"]
ALLOWED_ATTRS = {"a": ["href", "title", "rel", "target"], "img": ["src", "alt"]}


def sanitize_html(value: str) -> str:
    return bleach.clean(value or "", tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


class NewsCategory(TimeStampedModel):
    name_en = models.CharField(max_length=100)
    name_tet = models.CharField(max_length=100, blank=True)
    name_pt = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(max_length=110, unique=True, db_index=True)

    class Meta:
        verbose_name_plural = "News categories"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)


class PublishedNewsManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related("category", "author")
            .filter(is_published=True, published_at__lte=timezone.now())
        )


class NewsPost(TimeStampedModel):
    title_en = models.CharField(max_length=220)
    title_tet = models.CharField(max_length=220, blank=True)
    title_pt = models.CharField(max_length=220, blank=True)
    slug = models.SlugField(max_length=240, unique=True, db_index=True)

    excerpt_en = models.CharField(max_length=300, blank=True)
    excerpt_tet = models.CharField(max_length=300, blank=True)
    excerpt_pt = models.CharField(max_length=300, blank=True)

    content_en = models.TextField(blank=True)
    content_tet = models.TextField(blank=True)
    content_pt = models.TextField(blank=True)

    category = models.ForeignKey(
        NewsCategory, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="posts", db_index=True,
    )
    cover_image = models.ImageField(upload_to="news/", blank=True, null=True)
    author = models.ForeignKey(
        "accounts.AdminUser", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="news_posts",
    )

    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    views_count = models.PositiveIntegerField(default=0)

    objects = models.Manager()
    published = PublishedNewsManager()

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["is_published", "-published_at"]),
        ]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_en)[:220]
            slug, i = base, 1
            while NewsPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        self.content_en = sanitize_html(self.content_en)
        self.content_tet = sanitize_html(self.content_tet)
        self.content_pt = sanitize_html(self.content_pt)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
