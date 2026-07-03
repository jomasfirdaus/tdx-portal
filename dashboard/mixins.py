from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class StaffRequiredMixin(LoginRequiredMixin):
    """Any authenticated, active, non-locked staff account may pass."""
    login_url = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (not request.user.is_active or request.user.is_locked):
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Your account has been deactivated. Contact a super admin.")
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(StaffRequiredMixin, UserPassesTestMixin):
    """Restricts a view to super admins — used for staff accounts & audit log."""

    def test_func(self):
        return bool(self.request.user.is_authenticated and self.request.user.is_superadmin)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Super admin access required.")
        return super().handle_no_permission()


class OwnerActionLogMixin:
    """Attaches the current staff user to `author`/`created_by`-style fields, if present."""

    def form_valid(self, form):
        obj = form.instance
        if hasattr(obj, "author_id") and not obj.author_id:
            obj.author = self.request.user
        return super().form_valid(form)
