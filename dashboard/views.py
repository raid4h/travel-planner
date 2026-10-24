from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from .services import get_dashboard_chart_data, get_dashboard_overview


def _require_authenticated_or_redirect(request):
    if request.user.is_authenticated:
        return None
    try:
        login_url = reverse("accounts:login")
    except NoReverseMatch:
        login_url = "/admin/login/"
    query = urlencode({"next": request.get_full_path()})
    return redirect(f"{login_url}?{query}")


def dashboard_home(request):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    overview = get_dashboard_overview(request.user)
    chart_data = get_dashboard_chart_data(request.user)

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "overview": overview,
            "stats": overview["stats"],
            "chart_data": chart_data,
        },
    )

