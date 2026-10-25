from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Expense(models.Model):
    """An individual expense belonging to a Trip."""

    class Category(models.TextChoices):
        FOOD = "food", "Food"
        TRANSPORT = "transport", "Transport"
        ACCOMMODATION = "accommodation", "Accommodation"
        ACTIVITIES = "activities", "Activities"
        SHOPPING = "shopping", "Shopping"
        OTHER = "other", "Other"

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    title = models.CharField(max_length=150)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="expense_amount_greater_than_zero",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.get_category_display()})"

    def clean(self):
        errors = {}
        if self.amount is not None and self.amount <= 0:
            errors["amount"] = "Expense amount must be greater than zero."
        if self.title is not None and not self.title.strip():
            errors["title"] = "Expense title cannot be blank."
        if errors:
            raise ValidationError(errors)

