from django.urls import path

from . import views

app_name = "assessment"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("assessment/", views.assessment_dashboard, name="dashboard"),
    path("api/assessment/start/", views.api_start, name="api_start"),
    path("api/assessment/status/", views.api_status, name="api_status"),
    path("api/assessment/stop/", views.api_stop, name="api_stop"),
    path("api/assessment/duration/", views.api_duration, name="api_duration"),
    path("api/assessment/results/", views.api_results, name="api_results"),
    path("api/assessment/findings/", views.api_findings, name="api_findings"),
    path(
        "api/assessment/report/<str:report_format>/",
        views.api_report,
        name="api_report",
    ),
]
