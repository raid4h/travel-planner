from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import api_views, views

app_name = "budget"

router = SimpleRouter()
router.register("api/expenses", api_views.ExpenseViewSet, basename="expense")

urlpatterns = [
    path("budget/", views.budget_index, name="index"),
    path("trips/<int:trip_id>/budget/", views.expense_list, name="expense_list"),
    path("trips/<int:trip_id>/budget/set/", views.update_trip_budget, name="set_budget"),
    path("trips/<int:trip_id>/expenses/add/", views.expense_create, name="expense_create"),
    path(
        "trips/<int:trip_id>/expenses/<int:expense_id>/edit/",
        views.expense_edit,
        name="expense_edit",
    ),
    path(
        "trips/<int:trip_id>/expenses/<int:expense_id>/delete/",
        views.expense_delete,
        name="expense_delete",
    ),
    path(
        "api/trips/<int:trip_id>/budget/",
        api_views.TripBudgetSummaryAPIView.as_view(),
        name="api_trip_budget",
    ),
    path(
        "api/trips/<int:trip_id>/budget/ai-propose/",
        api_views.TripAIBudgetProposeAPIView.as_view(),
        name="api_ai_propose",
    ),
    path(
        "api/trips/<int:trip_id>/budget/ai-apply/",
        api_views.TripAIBudgetApplyAPIView.as_view(),
        name="api_ai_apply",
    ),
    path("", include(router.urls)),
]

