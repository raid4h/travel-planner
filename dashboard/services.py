from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from budget.models import Expense
from budget.services import CATEGORY_COLORS
from trips.models import Trip


def get_itinerary_status(trip):
    """
    Safely inspects itinerary relations on Trip so Dashboard works both before
    and after Member 3's itinerary models are merged.
    """
    candidate_attrs = ("itinerary_days", "days", "ai_plans", "itinerary_items", "activities")
    for attr in candidate_attrs:
        manager = getattr(trip, attr, None)
        if manager is not None and hasattr(manager, "count"):
            try:
                count = manager.count()
                if count > 0:
                    return {
                        "has_itinerary": True,
                        "count": count,
                        "label": "AI Plan Ready",
                    }
            except Exception:
                continue

    one_to_one = getattr(trip, "itinerary", None) or getattr(trip, "ai_plan", None)
    if one_to_one is not None:
        return {
            "has_itinerary": True,
            "count": 1,
            "label": "AI Plan Ready",
        }

    return {
        "has_itinerary": False,
        "count": 0,
        "label": "Not Generated",
    }


def _enrich_trip(trip):
    budget = trip.budget or Decimal("0.00")
    spent = trip.spent_total or Decimal("0.00")
    remaining = budget - spent
    is_over = remaining < Decimal("0.00")
    if budget > Decimal("0.00"):
        raw_pct = float((spent / budget) * Decimal("100"))
        percent_used = round(raw_pct, 1)
        bar_width = min(max(raw_pct, 0.0), 100.0)
    else:
        percent_used = 100.0 if spent > Decimal("0.00") else 0.0
        bar_width = 100.0 if spent > Decimal("0.00") else 0.0

    itinerary_info = get_itinerary_status(trip)
    return {
        "trip": trip,
        "id": trip.id,
        "title": trip.title,
        "destination": trip.destination,
        "country": trip.country,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "duration_days": trip.duration_days,
        "travelers": trip.travelers,
        "travel_style_display": trip.get_travel_style_display(),
        "status": trip.status,
        "currency": trip.currency,
        "budget": budget,
        "spent": spent,
        "remaining": remaining,
        "remaining_abs": abs(remaining),
        "is_over_budget": is_over,
        "percent_used": percent_used,
        "progress_bar_width": round(bar_width, 1),
        "expense_count": trip.expense_count,
        "itinerary_status": itinerary_info,
    }


def get_dashboard_overview(user):
    """Aggregates upcoming/current trips, budget totals, and recent expenses."""
    trips_qs = (
        Trip.objects.filter(owner=user, is_archived=False)
        .annotate(
            spent_total=Coalesce(Sum("expenses__amount"), Decimal("0.00")),
            expense_count=Count("expenses"),
        )
        .order_by("start_date")
    )

    ongoing_trips = []
    upcoming_trips = []
    completed_trips = []

    total_budget = Decimal("0.00")
    total_spent = Decimal("0.00")

    all_enriched = []
    for trip in trips_qs:
        item = _enrich_trip(trip)
        all_enriched.append(item)
        total_budget += item["budget"]
        total_spent += item["spent"]

        if item["status"] == "ongoing":
            ongoing_trips.append(item)
        elif item["status"] == "upcoming":
            upcoming_trips.append(item)
        else:
            completed_trips.append(item)

    total_remaining = total_budget - total_spent
    recent_expenses = (
        Expense.objects.filter(trip__owner=user, trip__is_archived=False)
        .select_related("trip")
        .order_by("-date", "-created_at")[:8]
    )

    return {
        "all_trips": all_enriched,
        "ongoing_trips": ongoing_trips,
        "upcoming_trips": upcoming_trips,
        "completed_trips": completed_trips,
        "recent_expenses": recent_expenses,
        "stats": {
            "total_trips": len(all_enriched),
            "ongoing_count": len(ongoing_trips),
            "upcoming_count": len(upcoming_trips),
            "completed_count": len(completed_trips),
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "total_remaining_abs": abs(total_remaining),
            "is_over_budget": total_remaining < Decimal("0.00"),
        },
    }


def get_dashboard_chart_data(user, trip_id=None):
    """Builds JSON-serializable Chart.js datasets for categories and per-trip budgets."""
    expenses_qs = Expense.objects.filter(trip__owner=user, trip__is_archived=False)
    trips_qs = Trip.objects.filter(owner=user, is_archived=False).order_by("start_date")

    if trip_id is not None:
        expenses_qs = expenses_qs.filter(trip_id=trip_id)

    cat_rows = {
        row["category"]: row["total"]
        for row in expenses_qs.values("category").annotate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )
    }

    cat_labels = []
    cat_values = []
    cat_colors = []
    for code, label in Expense.Category.choices:
        amount = cat_rows.get(code, Decimal("0.00"))
        cat_labels.append(label)
        cat_values.append(float(amount))
        cat_colors.append(CATEGORY_COLORS.get(code, "#6b7280"))

    annotated_trips = trips_qs.annotate(
        spent_total=Coalesce(Sum("expenses__amount"), Decimal("0.00"))
    )[:10]

    trip_labels = []
    trip_budgets = []
    trip_spent = []
    for trip in annotated_trips:
        trip_labels.append(trip.title[:28])
        trip_budgets.append(float(trip.budget or Decimal("0.00")))
        trip_spent.append(float(trip.spent_total or Decimal("0.00")))

    return {
        "category_chart": {
            "labels": cat_labels,
            "values": cat_values,
            "colors": cat_colors,
            "has_data": any(v > 0 for v in cat_values),
        },
        "trip_budget_chart": {
            "labels": trip_labels,
            "budgets": trip_budgets,
            "spent": trip_spent,
            "has_data": len(trip_labels) > 0,
        },
    }

