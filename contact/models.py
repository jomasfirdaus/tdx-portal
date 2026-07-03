from django.db import models

from core.models import TimeStampedModel


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    is_spam = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_read", "-created_at"])]

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject or '(no subject)'}"
