# =====================================================================
# File: trips/admin.py
# Purpose: Shows trips models in the Django admin site.
# Contains:
#   - TripAdmin: list columns, filters and search for Trips.
# =====================================================================

from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("title", "destination", "country", "owner", "start_date", "end_date", "is_archived")
    list_filter = ("is_archived", "travel_style", "country")
    search_fields = ("title", "destination", "owner__username")