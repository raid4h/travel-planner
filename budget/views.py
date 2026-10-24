from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from trips.models import Trip

from .forms import ExpenseForm, SetBudgetForm
from .models import Expense
from .services import get_trip_budget_summary, set_trip_budget


def _require_authenticated_or_redirect(request):
    """Redirects unauthenticated visitors to accounts:login (or /admin/login/ fallback)."""
    if request.user.is_authenticated:
        return None
    try:
        login_url = reverse("accounts:login")
    except NoReverseMatch:
        login_url = "/admin/login/"
    query = urlencode({"next": request.get_full_path()})
    return redirect(f"{login_url}?{query}")


def budget_index(request):
    """Redirects to the user's first active trip budget page, or renders an empty state."""
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    first_trip = (
        Trip.objects.filter(owner=request.user, is_archived=False)
        .order_by("start_date")
        .first()
    )
    if first_trip:
        return redirect("budget:expense_list", trip_id=first_trip.id)

    return render(
        request,
        "budget/expense_list.html",
        {
            "trip": None,
            "user_trips": [],
        },
    )


@ensure_csrf_cookie
def expense_list(request, trip_id):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
    user_trips = Trip.objects.filter(owner=request.user, is_archived=False).order_by(
        "start_date"
    )

    selected_category = request.GET.get("category", "").strip()
    expenses_qs = trip.expenses.all()
    valid_categories = {code for code, _ in Expense.Category.choices}
    if selected_category in valid_categories:
        expenses_qs = expenses_qs.filter(category=selected_category)
    else:
        selected_category = ""

    summary = get_trip_budget_summary(trip)
    budget_form = SetBudgetForm(initial={"budget": trip.budget})
    expense_form = ExpenseForm(initial={"date": trip.start_date})

    return render(
        request,
        "budget/expense_list.html",
        {
            "trip": trip,
            "user_trips": user_trips,
            "summary": summary,
            "expenses": expenses_qs,
            "selected_category": selected_category,
            "categories": Expense.Category.choices,
            "budget_form": budget_form,
            "expense_form": expense_form,
        },
    )


@require_POST
def update_trip_budget(request, trip_id):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
    form = SetBudgetForm(request.POST)
    if form.is_valid():
        set_trip_budget(trip, form.cleaned_data["budget"])
        messages.success(request, "Overall trip budget updated.")
    else:
        messages.error(request, "Please enter a valid non-negative budget amount.")
    return redirect("budget:expense_list", trip_id=trip.id)


def expense_create(request, trip_id):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.save()
            messages.success(request, f'Added expense "{expense.title}".')
            return redirect("budget:expense_list", trip_id=trip.id)
    else:
        form = ExpenseForm(initial={"date": trip.start_date})

    return render(
        request,
        "budget/expense_form.html",
        {
            "trip": trip,
            "form": form,
            "is_edit": False,
        },
    )


def expense_edit(request, trip_id, expense_id):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
    expense = get_object_or_404(Expense, pk=expense_id, trip=trip)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated expense "{expense.title}".')
            return redirect("budget:expense_list", trip_id=trip.id)
    else:
        form = ExpenseForm(instance=expense)

    return render(
        request,
        "budget/expense_form.html",
        {
            "trip": trip,
            "expense": expense,
            "form": form,
            "is_edit": True,
        },
    )


@require_POST
def expense_delete(request, trip_id, expense_id):
    auth_redirect = _require_authenticated_or_redirect(request)
    if auth_redirect:
        return auth_redirect

    trip = get_object_or_404(Trip, pk=trip_id, owner=request.user)
    expense = get_object_or_404(Expense, pk=expense_id, trip=trip)
    title = expense.title
    expense.delete()
    messages.success(request, f'Deleted expense "{title}".')
    return redirect("budget:expense_list", trip_id=trip.id)

