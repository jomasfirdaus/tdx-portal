from django.urls import path

from . import views

app_name = "dashboard"


def crud_urls(crud, namespace, pk_type="int"):
    return [
        path(f"{namespace}/", crud["list"].as_view(), name=f"{namespace}_list"),
        path(f"{namespace}/new/", crud["create"].as_view(), name=f"{namespace}_create"),
        path(f"{namespace}/<{pk_type}:pk>/edit/", crud["update"].as_view(), name=f"{namespace}_update"),
        path(f"{namespace}/<{pk_type}:pk>/delete/", crud["delete"].as_view(), name=f"{namespace}_delete"),
    ]


urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("site-profile/", views.SiteProfileUpdateView.as_view(), name="site_profile"),

    path("messages/", views.message_list, name="message_list"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),

    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),

    path("audit-log/", views.audit_log, name="audit_log"),
]

urlpatterns += crud_urls(views.page_header_crud, "page_header")
urlpatterns += crud_urls(views.location_crud, "location")
urlpatterns += crud_urls(views.service_area_crud, "service_area")
urlpatterns += crud_urls(views.appointment_slot_crud, "appointment_slot")
urlpatterns += crud_urls(views.core_value_crud, "core_value")
urlpatterns += crud_urls(views.statistic_crud, "statistic")
urlpatterns += crud_urls(views.department_crud, "department")
urlpatterns += crud_urls(views.team_member_crud, "team_member")
urlpatterns += crud_urls(views.program_category_crud, "program_category")
urlpatterns += crud_urls(views.program_crud, "program")
urlpatterns += crud_urls(views.news_category_crud, "news_category")
urlpatterns += crud_urls(views.news_post_crud, "news_post")
urlpatterns += crud_urls(views.album_crud, "album")
urlpatterns += crud_urls(views.photo_crud, "photo")
urlpatterns += crud_urls(views.staff_crud, "staff")
