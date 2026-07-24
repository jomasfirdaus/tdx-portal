import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ContactForm
from core.i18n import t as translate
from core.models import Location

security_logger = logging.getLogger("tdx.security")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


@require_http_methods(["GET", "POST"])
def contact_view(request):
    ip = _client_ip(request)
    lang = getattr(request, "LANGUAGE", "en")
    throttle_key = f"contact_throttle:{ip}"

    if request.method == "POST":
        if cache.get(throttle_key, 0) >= 5:
            messages.error(request, translate("contact.err_throttled", lang))
            return redirect("contact:contact")

        form = ContactForm(request.POST, lang=lang)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_address = ip
            obj.user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]
            obj.save()

            cache.set(throttle_key, cache.get(throttle_key, 0) + 1, timeout=600)

            try:
                send_mail(
                    subject=f"[TDx Website] New contact message: {obj.subject or 'No subject'}",
                    message=f"From: {obj.name} <{obj.email}>\nPhone: {obj.phone}\n\n{obj.message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_NOTIFY_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                security_logger.exception("contact_email_failed")

            messages.success(request, translate("contact.success", lang))
            return redirect("contact:contact")
    else:
        import time
        form = ContactForm(initial={"ts": time.time()}, lang=lang)

    locations = Location.objects.filter(is_active=True, show_on_map=True)
    return render(request, "public/contact.html", {"form": form, "locations": locations})
