from django.core.cache import cache
from django.shortcuts import render

from gallery.models import Album
from news.models import NewsPost
from programs.models import Program
from structure.models import Department, TeamMember

from .models import CoreValue, ServiceArea, SiteProfile, Statistic


def home(request):
    """
    Homepage: a handful of small, indexed queries, each capped with a
    LIMIT via slicing, and the aggregate result cached for a short window
    so repeated visits don't re-hit the database on every request.
    """
    cache_key = f"home_context:{request.LANGUAGE}"
    ctx = cache.get(cache_key)
    if ctx is None:
        ctx = {
            "profile": SiteProfile.get_solo(),
            "services": ServiceArea.objects.filter(is_active=True)[:6],
            "values": CoreValue.objects.filter(is_active=True)[:4],
            "stats": Statistic.objects.filter(is_active=True)[:4],
            "featured_programs": Program.published.filter(is_featured=True)[:3],
            "latest_news": NewsPost.published.all()[:3],
            "latest_album": Album.objects.filter(is_published=True).prefetch_related("photos").first(),
        }
        cache.set(cache_key, ctx, 120)
    return render(request, "public/home.html", ctx)


def profile(request):
    profile_obj = SiteProfile.get_solo()
    governance = (
        Department.objects.filter(is_active=True, category="governance")
        .prefetch_related("children")
    )
    org_tree = Department.objects.filter(is_active=True, parent__isnull=True).prefetch_related(
        "children__children"
    )
    return render(
        request,
        "public/profile.html",
        {"profile": profile_obj, "governance": governance, "org_tree": org_tree},
    )


def vision_mission(request):
    profile_obj = SiteProfile.get_solo()
    values = CoreValue.objects.filter(is_active=True)
    return render(request, "public/vision_mission.html", {"profile": profile_obj, "values": values})
