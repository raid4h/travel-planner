"""
destinations/views.py   (Raidah)

"Normal" Django views: they return finished HTML pages.
The JSON endpoints (search, save, weather) are in api_views.py.
"""
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

# Address of Member 3's "list itinerary stops" API, e.g. '/api/itinerary/items/'.
# Leave it empty until that endpoint exists. map.js expects each stop to look like:
# {title, day, order, latitude, longitude, start_time, category}
ITINERARY_STOPS_URL = ''


# ensure_csrf_cookie makes Django send a "csrftoken" cookie with this page.
# Our JavaScript (dest_utils.js) sends that token back on POST/DELETE requests.
# That is how Django knows the request really came from our own page.
@ensure_csrf_cookie
def destination_page(request):
    # render() fills the template with the data below and returns the finished HTML.
    return render(request, 'destinations/search.html', {
        'stops_url': ITINERARY_STOPS_URL,
    })