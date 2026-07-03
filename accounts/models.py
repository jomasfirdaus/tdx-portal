from django.contrib.auth.models import AbstractUser
from django.db import models


class AdminUser(AbstractUser):
    """
    Staff account for the custom TDx dashboard (NOT Django's built-in admin).
    Roles gate which sections of the dashboard a user may reach; see
    dashboard/permissions.py.
    """

    ROLE_SUPERADMIN = "superadmin"
    ROLE_EDITOR = "editor"
    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super Admin"),
        (ROLE_EDITOR, "Content Editor"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EDITOR, db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="staff/", blank=True, null=True)

    is_locked = models.BooleanField(default=False)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Staff account"

    @property
    def is_superadmin(self):
        return self.role == self.ROLE_SUPERADMIN or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class LoginActivity(models.Model):
    """Audit trail of authentication attempts against the staff dashboard."""

    username_attempt = models.CharField(max_length=150)
    user = models.ForeignKey(AdminUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="login_events")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True)
    success = models.BooleanField(default=False, db_index=True)
    reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["ip_address", "-created_at"])]
        verbose_name_plural = "Login activity"

    def __str__(self):
        status = "OK" if self.success else "FAILED"
        return f"[{status}] {self.username_attempt} @ {self.ip_address} ({self.created_at:%Y-%m-%d %H:%M})"
