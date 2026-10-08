from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def destination_page(request):
    return render(request, 'destinations/search.html')