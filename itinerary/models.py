from django.db import models
from trips.models import Trip


class AIPlan(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        GENERATED = "generated", "Generated"

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="ai_plans",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Plan - {self.trip.title}"


class ItineraryItem(models.Model):

    class ActivityType(models.TextChoices):
        FOOD = "food", "Food"
        SIGHTSEEING = "sightseeing", "Sightseeing"
        ACTIVITY = "activity", "Activity"
        TRANSPORT = "transport", "Transport"
        REST = "rest", "Rest"
        OTHER = "other", "Other"

    ai_plan = models.ForeignKey(
        AIPlan,
        on_delete=models.CASCADE,
        related_name="items",
    )

    day_number = models.PositiveIntegerField()
    time_block = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
        default=ActivityType.OTHER,
    )

    location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["day_number", "order"]

    def __str__(self):
        return self.title

