from rest_framework import serializers
from .models import Destination, WeatherCache


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'country', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'created_at']


class WeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherCache
        fields = ['forecast_date', 'temp_max', 'temp_min', 'condition', 'rain_probability', 'fetched_at']