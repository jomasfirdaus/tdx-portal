import logging

from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from accounts.models import AdminUser, LoginActivity
from appointments.models import AppointmentRequest, AppointmentSlot, AppointmentStatus
from contact.models import ContactMessage
from core.models import Location, PageHeader, SiteProfile
from gallery.models import Album, Photo
from news.models import NewsPost
from programs.models import Program
from structure.models import TeamMember

from .crud import build_crud_views, group_form_fields
from .forms import (
    AdminUserForm, AlbumForm, AppointmentSlotForm, CoreValueForm, DepartmentForm,
    NewsCategoryForm, NewsPostForm, PageHeaderForm, PhotoForm, ProgramCategoryForm, ProgramForm,
    ServiceAreaForm, LocationForm, SiteProfileForm, StatisticForm, TeamMemberForm,
)
from .mixins import StaffRequiredMixin, SuperAdminRequiredMixin
from core.models import CoreValue, ServiceArea, Statistic
from structure.models import Department
from programs.models import ProgramCategory
from news.models import NewsCategory

security_logger = logging.getLogger("tdx.security")


def dashboard_home(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    stats = {
        "programs": Program.objects.count(),
        "news": NewsPost.objects.count(),
        "team": TeamMember.objects.count(),
        "albums": Album.objects.count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
    }
    recent_messages = ContactMessage.objects.all()[:5]
    recent_logins = LoginActivity.objects.all()[:8]
    return render(
        request,
        "dashboard/home.html",
        {"stats": stats, "recent_messages": recent_messages, "recent_logins": recent_logins},
    )


class SiteProfileUpdateView(StaffRequiredMixin, UpdateView):
    model = SiteProfile
    form_class = SiteProfileForm
    template_name = "dashboard/site_profile_form.html"
    success_url = reverse_lazy("dashboard:site_profile")

    def get_object(self, queryset=None):
        return SiteProfile.get_solo()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["base_fields"], ctx["lang_fields"] = group_form_fields(ctx["form"])
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        cache.delete("site_profile_singleton")
        cache.delete("home_context:en")
        cache.delete("home_context:tet")
        cache.delete("home_context:pt")
        messages.success(self.request, "Site profile updated.")
        return response


# --- Contact inbox -----------------------------------------------------
def message_list(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    qs = ContactMessage.objects.all()
    from django.core.paginator import Paginator
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "dashboard/messages/list.html", {"page_obj": page_obj})


def message_detail(request, pk):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    obj = get_object_or_404(ContactMessage, pk=pk)
    if not obj.is_read:
        obj.is_read = True
        obj.save(update_fields=["is_read"])
    return render(request, "dashboard/messages/detail.html", {"message_obj": obj})


# --- Appointment requests -------------------------------------------------
# Deliberately NOT registered through build_crud_views(): a booking is
# patient-submitted data, not free-form editable content, so — same as
# ContactMessage above — staff get a review/status-change flow instead of a
# generic edit form that would let slot/date/contact details be silently
# rewritten.
def appointment_list(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    qs = AppointmentRequest.objects.select_related("slot__service_area", "location").all()
    status_filter = request.GET.get("status", "").strip()
    if status_filter in AppointmentStatus.values:
        qs = qs.filter(status=status_filter)
    from django.core.paginator import Paginator
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/appointments/list.html",
        {
            "page_obj": page_obj,
            "status_choices": AppointmentStatus.choices,
            "status_filter": status_filter,
        },
    )


def appointment_detail(request, pk):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    obj = get_object_or_404(
        AppointmentRequest.objects.select_related("slot__service_area", "location"), pk=pk
    )

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in AppointmentStatus.values:
            old_status = obj.status
            obj.status = new_status
            obj.save(update_fields=["status", "updated_at"])
            # Reuses the same logger AuditLogMiddleware writes dashboard
            # access records to — this is the minimal addition needed to
            # make status changes traceable, not a new audit subsystem.
            # NOTE: this still only produces a console/stdout log line, not
            # a queryable in-dashboard history — see the caveat in chat.
            security_logger.info(
                "appointment_status_changed id=%s from=%s to=%s by=%s",
                obj.pk, old_status, new_status, request.user.username,
            )
            messages.success(request, "Appointment status updated.")
            return redirect("dashboard:appointment_detail", pk=obj.pk)
        messages.error(request, "Invalid status value.")

    return render(
        request,
        "dashboard/appointments/detail.html",
        {"appointment": obj, "status_choices": AppointmentStatus.choices},
    )


# --- Appointment schedule (AppointmentSlot) — plain generic CRUD ----------
# Unlike AppointmentRequest above, a slot is staff-authored configuration
# data (like Location/ServiceArea), so the standard build_crud_views() set
# is the right fit here.
appointment_slot_crud = build_crud_views(
    model=AppointmentSlot, form_class=AppointmentSlotForm, url_namespace="appointment_slot",
    template_folder="generic",
    list_display=["service_area", "get_day_of_week_display", "start_time", "end_time", "capacity", "is_active"],
    search_fields=[], ordering=["service_area", "day_of_week", "start_time"],
)


# --- Staff accounts (super admin only) ----------------------------------
staff_crud = build_crud_views(
    model=AdminUser, form_class=AdminUserForm, url_namespace="staff",
    template_folder="generic", list_display=["username", "get_full_name", "role", "is_active"],
    search_fields=["username", "email", "first_name", "last_name"], ordering=["username"],
    superadmin_only=True,
)


def audit_log(request):
    if not (request.user.is_authenticated and request.user.is_superadmin):
        return redirect("accounts:login")
    from django.core.paginator import Paginator
    qs = LoginActivity.objects.all()
    page_obj = Paginator(qs, 40).get_page(request.GET.get("page"))
    return render(request, "dashboard/audit_log.html", {"page_obj": page_obj})


# --- Generic content CRUD sets -------------------------------------------
page_header_crud = build_crud_views(
    model=PageHeader, form_class=PageHeaderForm, url_namespace="page_header",
    template_folder="generic",
    list_display=["get_page_key_display", "title_en", "height", "is_active"],
    search_fields=["title_en"], ordering=["page_key"],
)
location_crud = build_crud_views(
    model=Location, form_class=LocationForm, url_namespace="location",
    template_folder="generic",
    list_display=["name_en", "phone", "is_primary", "order", "is_active"],
    search_fields=["name_en", "address_en"], ordering=["-is_primary", "order"],
)
service_area_crud = build_crud_views(
    model=ServiceArea, form_class=ServiceAreaForm, url_namespace="service_area",
    template_folder="generic", list_display=["name_en", "order", "is_active"],
    search_fields=["name_en"], ordering=["order"],
)
core_value_crud = build_crud_views(
    model=CoreValue, form_class=CoreValueForm, url_namespace="core_value",
    template_folder="generic", list_display=["name_en", "order", "is_active"],
    search_fields=["name_en"], ordering=["order"],
)
statistic_crud = build_crud_views(
    model=Statistic, form_class=StatisticForm, url_namespace="statistic",
    template_folder="generic", list_display=["label_en", "value", "order", "is_active"],
    search_fields=["label_en"], ordering=["order"],
)
department_crud = build_crud_views(
    model=Department, form_class=DepartmentForm, url_namespace="department",
    template_folder="generic", list_display=["name_en", "category", "order", "is_active"],
    search_fields=["name_en"], ordering=["order"],
)
team_member_crud = build_crud_views(
    model=TeamMember, form_class=TeamMemberForm, url_namespace="team_member",
    template_folder="generic",
    list_display=["full_name", "role_title_en", "is_board_member", "is_leadership", "is_published"],
    search_fields=["full_name", "role_title_en"], ordering=["order"],
)
program_category_crud = build_crud_views(
    model=ProgramCategory, form_class=ProgramCategoryForm, url_namespace="program_category",
    template_folder="generic", list_display=["name_en"], search_fields=["name_en"], ordering=["name_en"],
)
program_crud = build_crud_views(
    model=Program, form_class=ProgramForm, url_namespace="program",
    template_folder="generic",
    list_display=["title_en", "status", "is_featured", "is_published"],
    search_fields=["title_en"], ordering=["-created_at"],
)
news_category_crud = build_crud_views(
    model=NewsCategory, form_class=NewsCategoryForm, url_namespace="news_category",
    template_folder="generic", list_display=["name_en"], search_fields=["name_en"], ordering=["name_en"],
)
news_post_crud = build_crud_views(
    model=NewsPost, form_class=NewsPostForm, url_namespace="news_post",
    template_folder="generic",
    list_display=["title_en", "category", "is_published", "published_at"],
    search_fields=["title_en"], ordering=["-published_at"],
)
album_crud = build_crud_views(
    model=Album, form_class=AlbumForm, url_namespace="album",
    template_folder="generic", list_display=["title_en", "event_date", "is_published"],
    search_fields=["title_en"], ordering=["-event_date"],
)
photo_crud = build_crud_views(
    model=Photo, form_class=PhotoForm, url_namespace="photo",
    template_folder="generic", list_display=["album", "order"],
    search_fields=[], ordering=["album", "order"],
)
