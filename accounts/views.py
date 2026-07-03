import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from .forms import StaffLoginForm, StaffSetPasswordForm
from .models import LoginActivity

security_logger = logging.getLogger("tdx.security")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _throttle_key(ip, username):
    return f"login_throttle:{ip}:{username.lower()}"


@never_cache
@csrf_protect
def staff_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    form = StaffLoginForm(request.POST or None)
    ip = _client_ip(request)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        key = _throttle_key(ip, username)
        attempts = cache.get(key, 0)

        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            security_logger.warning("login_locked_out username=%s ip=%s", username, ip)
            messages.error(
                request,
                f"Too many failed attempts. Try again in {settings.LOGIN_LOCKOUT_MINUTES} minutes.",
            )
            LoginActivity.objects.create(
                username_attempt=username, ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                success=False, reason="locked_out",
            )
            return render(request, "accounts/login.html", {"form": form})

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active and not user.is_locked:
            login(request, user)
            cache.delete(key)
            request.session.cycle_key()  # rotate session id on privilege change
            LoginActivity.objects.create(
                username_attempt=username, user=user, ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                success=True,
            )
            security_logger.info("login_success username=%s ip=%s", username, ip)
            return redirect(request.GET.get("next") or "dashboard:home")

        cache.set(key, attempts + 1, timeout=settings.LOGIN_LOCKOUT_MINUTES * 60)
        LoginActivity.objects.create(
            username_attempt=username, ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            success=False, reason="bad_credentials",
        )
        security_logger.warning("login_failed username=%s ip=%s", username, ip)
        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"form": form})


@login_required
def staff_logout(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("core:home")


class StaffPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StaffSetPasswordForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        messages.success(self.request, "Password updated successfully.")
        return super().form_valid(form)
