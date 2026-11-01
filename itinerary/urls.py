from django.urls import path
from . import api_views, views

app_name = "itinerary"

urlpatterns = [
    # Frontend planner page
    path("itinerary/planner/", views.planner_page, name="planner"),

    # AI Itinerary APIs
    path(
        "api/itineraries/",
        api_views.AIPlanListCreateView.as_view(),
        name="ai-plan-list"
    ),
    path(
        "api/itineraries/<int:pk>/",
        api_views.AIPlanDetailView.as_view(),
        name="ai-plan-detail"
    ),
    path(
        "api/itineraries/generate/",
        api_views.GenerateItineraryView.as_view(),
        name="generate-itinerary"
    ),
]