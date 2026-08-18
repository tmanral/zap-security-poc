from django.urls import path

from . import views

app_name = "assessment"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("assessment/", views.assessment_dashboard, name="dashboard"),
]
