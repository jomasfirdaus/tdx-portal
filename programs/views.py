from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Program, ProgramCategory


def program_list(request):
    qs = Program.published.all()

    category_slug = request.GET.get("category")
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    status = request.GET.get("status")
    if status in dict(Program.STATUS_CHOICES):
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = ProgramCategory.objects.all()
    return render(
        request,
        "public/programs_list.html",
        {"page_obj": page_obj, "categories": categories, "active_category": category_slug, "active_status": status},
    )


def program_detail(request, slug):
    obj = get_object_or_404(Program.published.all(), slug=slug)
    related = (
        Program.published.exclude(pk=obj.pk)
        .filter(category=obj.category)[:3]
        if obj.category_id else Program.published.exclude(pk=obj.pk)[:3]
    )
    return render(request, "public/program_detail.html", {"program": obj, "related": related})
