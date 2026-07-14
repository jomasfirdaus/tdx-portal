from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointment_view, name="appointment"),
    path("availability/", views.slot_availability_view, name="availability"),
]
