import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim requires an identifying User-Agent. CHANGE THE EMAIL to your real one.
USER_AGENT = "TravelPlannerUniProject/1.0 (softeng327@gmail.com)"


class GeocodingError(Exception):
    pass


def search_places(query, limit=5):
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "limit": limit, "addressdetails": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise GeocodingError("Search service is unavailable. Try again shortly.") from exc

    results = []
    for item in resp.json():
        address = item.get("address", {})
        results.append({
            "name": item.get("name") or item.get("display_name", "").split(",")[0],
            "display_name": item.get("display_name", ""),
            "country": address.get("country", ""),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
        })
    return results