from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.models import Trip

from .models import Expense
from .serializers import ExpenseSerializer, TripBudgetUpdateSerializer
from .services import (
    AIBudgetError,
    apply_ai_proposal,
    get_trip_budget_summary,
    propose_trip_budget_with_ai,
    set_trip_budget,
)


def _serialize_summary(summary):
    """Converts Decimal values in get_trip_budget_summary for JSON responses."""
    return {
        "trip_id": summary["trip_id"],
        "currency": summary["currency"],
        "total_budget": str(summary["total_budget"]),
        "total_spent": str(summary["total_spent"]),
        "remaining_budget": str(summary["remaining_budget"]),
        "remaining_abs": str(summary["remaining_abs"]),
        "expense_count": summary["expense_count"],
        "is_over_budget": summary["is_over_budget"],
        "percent_used": summary["percent_used"],
        "progress_bar_width": summary["progress_bar_width"],
        "category_breakdown": [
            {
                "category": item["category"],
                "label": item["label"],
                "amount": str(item["amount"]),
                "count": item["count"],
                "percentage": item["percentage"],
                "color": item["color"],
            }
            for item in summary["category_breakdown"]
        ],
    }


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Expense.objects.filter(trip__owner=self.request.user).select_related("trip")
        trip_id = self.request.query_params.get("trip")
        category = self.request.query_params.get("category")
        if trip_id and trip_id.isdigit():
            qs = qs.filter(trip_id=int(trip_id))
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]
        if trip.owner_id != self.request.user.id:
            raise PermissionDenied("You can only add expenses to your own trips.")
        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.validated_data.get("trip", serializer.instance.trip)
        if trip.owner_id != self.request.user.id:
            raise PermissionDenied("You can only modify expenses on your own trips.")
        serializer.save()


class TripBudgetSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_trip(self, request, trip_id):
        return get_object_or_404(Trip, pk=trip_id, owner=request.user)

    def get(self, request, trip_id):
        trip = self._get_trip(request, trip_id)
        summary = get_trip_budget_summary(trip)
        expenses = ExpenseSerializer(trip.expenses.all(), many=True).data
        return Response(
            {
                "summary": _serialize_summary(summary),
                "expenses": expenses,
            }
        )

    def patch(self, request, trip_id):
        trip = self._get_trip(request, trip_id)
        serializer = TripBudgetUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_trip_budget(trip, serializer.validated_data["budget"])
        summary = get_trip_budget_summary(trip)
        return Response({"summary": _serialize_summary(summary)})


class TripAIBudgetProposeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
        try:
            proposal = propose_trip_budget_with_ai(trip)
        except AIBudgetError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(proposal)


class TripAIBudgetApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
        apply_budget_flag = bool(request.data.get("apply_budget", True))
        apply_expenses_flag = bool(request.data.get("apply_expenses", False))
        replace_existing_ai = bool(request.data.get("replace_existing_ai", True))

        rec_budget = (
            request.data.get("recommended_total_budget") if apply_budget_flag else None
        )
        proposed_items = (
            request.data.get("proposed_expenses") if apply_expenses_flag else None
        )

        created = apply_ai_proposal(
            trip,
            recommended_budget=rec_budget,
            proposed_expenses=proposed_items,
            replace_existing_ai=replace_existing_ai,
        )
        trip.refresh_from_db()
        summary = get_trip_budget_summary(trip)
        expenses = ExpenseSerializer(trip.expenses.all(), many=True).data
        return Response(
            {
                "applied_expenses_count": len(created),
                "summary": _serialize_summary(summary),
                "expenses": expenses,
            }
        )

