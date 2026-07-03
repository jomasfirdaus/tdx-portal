from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Album


def album_list(request):
    qs = Album.objects.filter(is_published=True)
    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "public/gallery_list.html", {"page_obj": page_obj})


def album_detail(request, slug):
    obj = get_object_or_404(
        Album.objects.filter(is_published=True).prefetch_related("photos"), slug=slug
    )
    return render(request, "public/gallery_detail.html", {"album": obj})
