# =====================================================================
# File: trips/models.py
# Purpose: Database model for a trip (the central table of the app).
# Contains:
#   - Trip: one planned trip, owned by one user. Holds destination,
#     dates, travelers, travel style, interest tags, budget, notes
#     and the archived flag.
#   - Trip.status / Trip.duration_days: values calculated from dates.
#   - Trip.clean(): friendly validation used by forms and the admin.
# =====================================================================

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Trip(models.Model):
    """A trip planned by a user. Every trip belongs to exactly one owner."""

    class TravelStyle(models.TextChoices):
        BUDGET = "budget", "Budget"
        BALANCED = "balanced", "Balanced"
        LUXURY = "luxury", "Luxury"
        ADVENTURE = "adventure", "Adventure"
        RELAXED = "relaxed", "Relaxed"

    # Quick-pick suggestions shown as chips in the form. Users can also
    # type any tag they like (e.g. "Shrines"), so these are NOT enforced.
    SUGGESTED_INTERESTS = [
        "Food", "Culture", "Nature", "Adventure",
        "Nightlife", "Shopping", "History", "Relaxation",
    ]
    MAX_INTERESTS = 15
    MAX_INTEREST_LENGTH = 40

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips",
    )
    title = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    country = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    travelers = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    travel_style = models.CharField(
        max_length=20,
        choices=TravelStyle.choices,
        default=TravelStyle.BALANCED,
    )
    interests = models.JSONField(default=list, blank=True)
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="USD")
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="trip_end_date_not_before_start_date",
            ),
            models.CheckConstraint(
                condition=Q(travelers__gte=1),
                name="trip_travelers_at_least_one",
            ),
            models.CheckConstraint(
                condition=Q(budget__gte=0),
                name="trip_budget_not_negative",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.destination})"

    def clean(self):
        errors = {}

        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be before the start date."

        # Interests: a list of free-text tags. Trim, drop blanks and duplicates.
        tags = []
        for raw in self.interests or []:
            tag = str(raw).strip()
            if tag and tag.lower() not in (t.lower() for t in tags):
                tags.append(tag)
        if len(tags) > self.MAX_INTERESTS:
            errors["interests"] = f"Please use at most {self.MAX_INTERESTS} interests."
        elif any(len(t) > self.MAX_INTEREST_LENGTH for t in tags):
            errors["interests"] = (
                f"Each interest must be {self.MAX_INTEREST_LENGTH} characters or fewer."
            )
        self.interests = tags

        if self.currency:
            self.currency = self.currency.strip().upper()
            if len(self.currency) != 3 or not self.currency.isalpha():
                errors["currency"] = "Use a 3-letter currency code, e.g. USD."

        if errors:
            raise ValidationError(errors)

    @property
    def duration_days(self):
        """Number of days the trip lasts (start and end day both count)."""
        return (self.end_date - self.start_date).days + 1

    @property
    def status(self):
        """Calculated from the dates, so it is never out of date."""
        today = timezone.localdate()
        if today < self.start_date:
            return "upcoming"
        if today > self.end_date:
            return "completed"
        return "ongoing"