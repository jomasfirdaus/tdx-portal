from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import NewsCategory, NewsPost


def news_list(request):
    qs = NewsPost.published.all()

    category_slug = request.GET.get("category")
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    q = request.GET.get("q", "").strip()
    if q:
        # Simple, safe substring search via the ORM (parameterized — no raw SQL).
        from django.db.models import Q
        qs = qs.filter(
            Q(title_en__icontains=q) | Q(title_tet__icontains=q) | Q(title_pt__icontains=q)
        )

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    categories = NewsCategory.objects.all()
    return render(
        request,
        "public/news_list.html",
        {"page_obj": page_obj, "categories": categories, "active_category": category_slug, "q": q},
    )


def news_detail(request, slug):
    obj = get_object_or_404(NewsPost.published.all(), slug=slug)
    # Atomic counter increment at the DB level — avoids a read-modify-write race.
    NewsPost.objects.filter(pk=obj.pk).update(views_count=F("views_count") + 1)
    related = NewsPost.published.exclude(pk=obj.pk).filter(category=obj.category)[:3]
    return render(request, "public/news_detail.html", {"post": obj, "related": related})
