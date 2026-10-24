from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "trip",
        "category",
        "amount",
        "date",
        "is_ai_generated",
        "created_at",
    )
    list_filter = ("category", "is_ai_generated", "date")
    search_fields = ("title", "notes", "trip__title", "trip__destination")
    ordering = ("-date", "-created_at")

