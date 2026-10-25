import json
import os
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from trips.models import Trip

from .models import Expense
from .services import (
    GeminiKeyRotator,
    apply_ai_proposal,
    get_trip_budget_summary,
    propose_trip_budget_with_ai,
    set_trip_budget,
)

User = get_user_model()


class BudgetAndExpenseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alimul", password="password123")
        self.other_user = User.objects.create_user(username="other", password="password123")
        today = timezone.localdate()
        self.trip = Trip.objects.create(
            owner=self.user,
            title="Tokyo Autumn Adventure",
            destination="Tokyo",
            country="Japan",
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=10),
            travelers=2,
            travel_style=Trip.TravelStyle.BALANCED,
            interests=["food", "culture"],
            budget=Decimal("3000.00"),
            currency="USD",
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

    def test_budget_summary_orm_calculations(self):
        Expense.objects.create(
            trip=self.trip,
            title="Flights",
            category=Expense.Category.TRANSPORT,
            amount=Decimal("1100.00"),
        )
        Expense.objects.create(
            trip=self.trip,
            title="Hotel Shinjuku",
            category=Expense.Category.ACCOMMODATION,
            amount=Decimal("680.00"),
        )
        Expense.objects.create(
            trip=self.trip,
            title="Sushi Dinner",
            category=Expense.Category.FOOD,
            amount=Decimal("120.00"),
        )

        summary = get_trip_budget_summary(self.trip)
        self.assertEqual(summary["total_budget"], Decimal("3000.00"))
        self.assertEqual(summary["total_spent"], Decimal("1900.00"))
        self.assertEqual(summary["remaining_budget"], Decimal("1100.00"))
        self.assertFalse(summary["is_over_budget"])
        self.assertEqual(summary["expense_count"], 3)

    def test_set_budget_and_over_budget_flag(self):
        set_trip_budget(self.trip, "500.00")
        Expense.objects.create(
            trip=self.trip,
            title="Luxury Ryokan",
            category=Expense.Category.ACCOMMODATION,
            amount=Decimal("650.00"),
        )
        summary = get_trip_budget_summary(self.trip)
        self.assertTrue(summary["is_over_budget"])
        self.assertEqual(summary["remaining_budget"], Decimal("-150.00"))
        self.assertEqual(summary["remaining_abs"], Decimal("150.00"))

    def test_expense_crud_and_ownership_protection(self):
        # Create via API
        resp = self.api.post(
            "/api/expenses/",
            {
                "trip": self.trip.id,
                "title": "Bullet Train",
                "category": "transport",
                "amount": "220.00",
                "date": str(self.trip.start_date),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        exp_id = resp.data["id"]

        # Another user cannot read or delete this expense
        other_api = APIClient()
        other_api.force_authenticate(user=self.other_user)
        forbidden_resp = other_api.delete(f"/api/expenses/{exp_id}/")
        self.assertEqual(forbidden_resp.status_code, 404)

        # Owner can update and delete
        patch_resp = self.api.patch(
            f"/api/expenses/{exp_id}/", {"amount": "250.00"}, format="json"
        )
        self.assertEqual(patch_resp.status_code, 200)
        del_resp = self.api.delete(f"/api/expenses/{exp_id}/")
        self.assertEqual(del_resp.status_code, 204)
        self.assertEqual(self.trip.expenses.count(), 0)

    def test_round_robin_key_rotator_and_429_failover(self):
        rotator = GeminiKeyRotator()
        with patch.dict(os.environ, {"GEMINI_API_KEYS": "keyA, keyB, keyC", "GEMINI_API_KEY": ""}):
            self.assertEqual(rotator.get_ordered_keys_for_request(), ["keyA", "keyB", "keyC"])
            self.assertEqual(rotator.get_ordered_keys_for_request(), ["keyB", "keyC", "keyA"])
            self.assertEqual(rotator.get_ordered_keys_for_request(), ["keyC", "keyA", "keyB"])
            self.assertEqual(rotator.get_ordered_keys_for_request(), ["keyA", "keyB", "keyC"])

        # Test automatic failover when first key hits HTTP 429 rate limit
        rate_limited_resp = MagicMock(status_code=429)
        rate_limited_resp.json.return_value = {"error": {"message": "Quota exceeded"}}

        ai_payload = {
            "recommended_total_budget": 2400,
            "summary": "Balanced 6-day Tokyo estimate for 2 travelers.",
            "categories": [
                {"category": "accommodation", "estimated_amount": 1000, "rationale": "5 nights hotel"},
                {"category": "food", "estimated_amount": 500, "rationale": "Local dining"},
            ],
            "proposed_expenses": [
                {
                    "title": "Shinjuku Hotel (5 nights)",
                    "category": "accommodation",
                    "amount": 1000,
                    "notes": "Mid-range twin room",
                },
                {
                    "title": "Daily Meals & Street Food",
                    "category": "food",
                    "amount": 500,
                    "notes": "2 travelers",
                },
            ],
        }
        ok_resp = MagicMock(status_code=200)
        ok_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"thought": True, "text": "Thinking about Tokyo prices..."},
                            {"text": json.dumps(ai_payload)},
                        ]
                    }
                }
            ]
        }

        with patch.dict(os.environ, {"GEMINI_API_KEYS": "limited_key,working_key", "GEMINI_API_KEY": ""}):
            with patch("budget.services.requests.post", side_effect=[rate_limited_resp, ok_resp]) as mock_post:
                proposal = propose_trip_budget_with_ai(self.trip)
                self.assertEqual(mock_post.call_count, 2)
                self.assertEqual(proposal["recommended_total_budget"], "2400.00")
                self.assertEqual(len(proposal["proposed_expenses"]), 2)

                # Apply proposal to DB
                created = apply_ai_proposal(
                    self.trip,
                    recommended_budget=proposal["recommended_total_budget"],
                    proposed_expenses=proposal["proposed_expenses"],
                )
                self.trip.refresh_from_db()
                self.assertEqual(self.trip.budget, Decimal("2400.00"))
                self.assertEqual(len(created), 2)
                self.assertTrue(all(e.is_ai_generated for e in created))

    def test_budget_html_views(self):
        self.client.force_login(self.user)
        url = reverse("budget:expense_list", kwargs={"trip_id": self.trip.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Tokyo Autumn Adventure")

