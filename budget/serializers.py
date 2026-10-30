from decimal import Decimal

from rest_framework import serializers

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "trip",
            "title",
            "category",
            "category_display",
            "amount",
            "date",
            "notes",
            "is_ai_generated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category_display", "created_at", "updated_at"]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_title(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be blank.")
        return cleaned


class TripBudgetUpdateSerializer(serializers.Serializer):
    budget = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )

