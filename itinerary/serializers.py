from rest_framework import serializers
from .models import AIPlan, ItineraryItem


class ItineraryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryItem
        fields = "__all__"


class AIPlanSerializer(serializers.ModelSerializer):
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = AIPlan
        fields = "__all__"
