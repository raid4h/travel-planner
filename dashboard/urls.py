from django.urls import path

from . import api_views, views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.dashboard_home, name="home"),
    path(
        "api/dashboard/stats/",
        api_views.DashboardStatsAPIView.as_view(),
        name="api_stats",
    ),
]

