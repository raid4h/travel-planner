from django.contrib import admin
from .models import AIPlan, ItineraryItem


class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 0


@admin.register(AIPlan)
class AIPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "status", "created_at")
    list_filter = ("status", "created_at")
    inlines = [ItineraryItemInline]


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "ai_plan",
        "day_number",
        "time_block",
        "activity_type",
    )
    list_filter = ("activity_type", "day_number")