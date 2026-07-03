from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path


def robots_txt(request):
    content = (
        "User-agent: *\n"
        f"Disallow: /{settings.DASHBOARD_URL_PREFIX}/\n"
        "Disallow: /accounts/\n"
    )
    return HttpResponse(content, content_type="text/plain")


urlpatterns = [
    path("", include("core.urls")),
    path("programs/", include("programs.urls")),
    path("team-structure/", include("structure.urls")),
    path("news/", include("news.urls")),
    path("gallery/", include("gallery.urls")),
    path("contact/", include("contact.urls")),
    path("accounts/", include("accounts.urls")),
    path(f"{settings.DASHBOARD_URL_PREFIX}/", include("dashboard.urls")),
    path("robots.txt", robots_txt),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.error_views.error_404"
handler500 = "core.error_views.error_500"
