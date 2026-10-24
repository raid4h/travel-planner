from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from budget.models import Expense
from trips.models import Trip

from .services import get_dashboard_chart_data, get_dashboard_overview

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alimul_dash", password="password123")
        today = timezone.localdate()

        self.ongoing_trip = Trip.objects.create(
            owner=self.user,
            title="Current Kyoto Trip",
            destination="Kyoto",
            country="Japan",
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=3),
            travelers=2,
            budget=Decimal("2000.00"),
            currency="USD",
        )
        self.upcoming_trip = Trip.objects.create(
            owner=self.user,
            title="Upcoming Bali Escape",
            destination="Bali",
            country="Indonesia",
            start_date=today + timedelta(days=20),
            end_date=today + timedelta(days=27),
            travelers=1,
            budget=Decimal("1500.00"),
            currency="USD",
        )
        Expense.objects.create(
            trip=self.ongoing_trip,
            title="Kyoto Ryokan",
            category=Expense.Category.ACCOMMODATION,
            amount=Decimal("600.00"),
        )
        Expense.objects.create(
            trip=self.ongoing_trip,
            title="Matcha Tasting",
            category=Expense.Category.FOOD,
            amount=Decimal("50.00"),
        )

    def test_dashboard_overview_and_stats(self):
        overview = get_dashboard_overview(self.user)
        stats = overview["stats"]

        self.assertEqual(stats["total_trips"], 2)
        self.assertEqual(stats["ongoing_count"], 1)
        self.assertEqual(stats["upcoming_count"], 1)
        self.assertEqual(stats["total_budget"], Decimal("3500.00"))
        self.assertEqual(stats["total_spent"], Decimal("650.00"))
        self.assertEqual(stats["total_remaining"], Decimal("2850.00"))
        self.assertEqual(len(overview["recent_expenses"]), 2)

    def test_dashboard_chart_data(self):
        charts = get_dashboard_chart_data(self.user)
        self.assertTrue(charts["category_chart"]["has_data"])
        self.assertTrue(charts["trip_budget_chart"]["has_data"])
        self.assertEqual(len(charts["trip_budget_chart"]["labels"]), 2)

    def test_dashboard_page_and_stats_api(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Current Kyoto Trip")
        self.assertContains(resp, "Upcoming Bali Escape")

        api_resp = self.client.get(reverse("dashboard:api_stats"))
        self.assertEqual(api_resp.status_code, 200)
        self.assertEqual(api_resp.json()["stats"]["total_spent"], "650.00")

