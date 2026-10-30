"""
destinations/services/geocoding.py   (Raidah)

BACKEND service: turns a place name typed by the user ("Tokyo") into
coordinates by asking OpenStreetMap's free geocoder, called Nominatim.
Only this Python code talks to Nominatim; the browser never does.
"""
import logging
import requests

# A logger lets us print technical details to the terminal
# without showing them to the user on the page.
logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim's usage policy requires a User-Agent that identifies our app.
# CHANGE THE EMAIL to your real one.
USER_AGENT = "TravelPlannerUniProject/1.0 (softeng327@gmail.com)"

# Language for the place names we get back. Without this, Nominatim answers in
# the place's LOCAL language (Tokyo -> "東京都"). "en" makes it answer in English.
LANGUAGE = "en"


class GeocodingError(Exception):
    """Raised when the geocoding service cannot be reached."""


def search_places(query, limit=5):
    """Return up to `limit` matching places as a list of simple dictionaries."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": query,                  # what the user typed
                "format": "jsonv2",          # ask for JSON
                "limit": limit,
                "addressdetails": 1,         # include the country in the answer
                "accept-language": LANGUAGE, # English place names
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,                      # never wait more than 10 seconds
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        # Print the REAL reason (e.g. "403 Client Error: Forbidden") in the terminal.
        # The user only sees the friendly message below.
        logger.warning("Nominatim request failed: %s", exc)
        raise GeocodingError("Search service is unavailable. Try again shortly.") from exc

    results = []
    for item in resp.json():
        address = item.get("address", {})
        display_name = item.get("display_name", "")  # already in English, e.g. "Tokyo, Japan"
        results.append({
            # The first part of display_name is the place's name in English.
            # If it is empty, fall back to the raw "name" field.
            "name": display_name.split(",")[0].strip() or item.get("name", ""),
            "display_name": display_name,
            "country": address.get("country", ""),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
        })
    return results