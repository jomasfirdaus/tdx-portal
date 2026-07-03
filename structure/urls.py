from django.urls import path

from . import views

app_name = "structure"

urlpatterns = [
    path("", views.team_structure, name="team"),
]
