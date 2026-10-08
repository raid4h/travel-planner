from datetime import date, timedelta

import requests
from django.utils import timezone

from ..models import WeatherCache

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_HOURS = 3

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


class WeatherError(Exception):
    pass


def get_forecast(destination, days=7):
    upcoming = WeatherCache.objects.filter(destination=destination, forecast_date__gte=date.today())
    fresh_after = timezone.now() - timedelta(hours=CACHE_HOURS)

    # 1. Fresh cache? Return it without calling the API.
    fresh = upcoming.filter(fetched_at__gte=fresh_after)
    if fresh.count() >= days:
        return list(fresh[:days])

    # 2. Otherwise ask Open-Meteo and store the result.
    try:
        resp = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": destination.latitude,
                "longitude": destination.longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=10,
        )
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        # 3. If the API is down, use old cached data if we have any.
        stale = list(upcoming[:days])
        if stale:
            return stale
        raise WeatherError("Weather service is unavailable. Try again shortly.") from exc

    for i, day_str in enumerate(daily["time"]):
        WeatherCache.objects.update_or_create(
            destination=destination,
            forecast_date=date.fromisoformat(day_str),
            defaults={
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "condition": WEATHER_CODES.get(daily["weather_code"][i], "Unknown"),
                "rain_probability": daily["precipitation_probability_max"][i],
            },
        )
    return list(upcoming[:days])