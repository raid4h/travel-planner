# =====================================================================
# File: trips/views.py
# Purpose: The "controllers" for the trip pages. Every view requires a
#          logged-in user and only ever touches THAT user's own trips
#          (someone else's trip gives a 404 "not found" page).
# Contains:
#   - TripListView:   "My Trips" page with search and status filters
#   - TripCreateView: "New Trip" form
#   - TripDetailView: one trip's full details
#   - TripUpdateView: "Edit Trip" form
#   - TripDeleteView: "Are you sure?" page, then deletes the trip
#   - toggle_archive: archive / restore a trip (POST only)
# =====================================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import TripForm
from .models import Trip

# The filter tabs on the list page: (value in the URL, label shown).
FILTERS = [
    ("all", "All"),
    ("upcoming", "Upcoming"),
    ("ongoing", "Ongoing"),
    ("completed", "Completed"),
    ("archived", "Archived"),
]


class OwnerTripsMixin(LoginRequiredMixin):
    """Logged-in users only, and only their own trips."""

    model = Trip

    def get_queryset(self):
        return Trip.objects.filter(owner=self.request.user)


class TripListView(OwnerTripsMixin, ListView):
    template_name = "trips/trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        trips = super().get_queryset()
        today = timezone.localdate()
        current = self.request.GET.get("filter", "all")
        search = self.request.GET.get("q", "").strip()

        if current == "archived":
            trips = trips.filter(is_archived=True)
        else:
            trips = trips.filter(is_archived=False)
            if current == "upcoming":
                trips = trips.filter(start_date__gt=today)
            elif current == "ongoing":
                trips = trips.filter(start_date__lte=today, end_date__gte=today)
            elif current == "completed":
                trips = trips.filter(end_date__lt=today)

        if search:
            trips = trips.filter(
                Q(title__icontains=search)
                | Q(destination__icontains=search)
                | Q(country__icontains=search)
            )
        return trips

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current = self.request.GET.get("filter", "all")
        if current not in dict(FILTERS):
            current = "all"

        # Numbers shown on the tabs (ignores the search box).
        today = timezone.localdate()
        mine = Trip.objects.filter(owner=self.request.user)
        active = mine.filter(is_archived=False)
        counts = {
            "all": active.count(),
            "upcoming": active.filter(start_date__gt=today).count(),
            "ongoing": active.filter(start_date__lte=today, end_date__gte=today).count(),
            "completed": active.filter(end_date__lt=today).count(),
            "archived": mine.filter(is_archived=True).count(),
        }
        context["filters"] = [(key, label, counts[key]) for key, label in FILTERS]
        context["current_filter"] = current
        context["search"] = self.request.GET.get("q", "").strip()
        context["total_trips"] = sum(
            counts[k] for k in ("all", "archived")
        )  # 0 means the user has never made a trip -> big empty state
        return context


class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = "trips/trip_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user  # the owner is always YOU
        messages.success(self.request, "Trip created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("trips:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class TripDetailView(OwnerTripsMixin, DetailView):
    template_name = "trips/trip_detail.html"
    context_object_name = "trip"


class TripUpdateView(OwnerTripsMixin, UpdateView):
    form_class = TripForm
    template_name = "trips/trip_form.html"
    context_object_name = "trip"

    def form_valid(self, form):
        messages.success(self.request, "Trip updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("trips:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class TripDeleteView(OwnerTripsMixin, DeleteView):
    template_name = "trips/trip_confirm_delete.html"
    context_object_name = "trip"
    success_url = reverse_lazy("trips:list")

    def form_valid(self, form):
        messages.success(self.request, f"Deleted “{self.object.title}”.")
        return super().form_valid(form)


@login_required
@require_POST
def toggle_archive(request, pk):
    """Archive a trip, or restore it if it is already archived."""
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    trip.is_archived = not trip.is_archived
    trip.save(update_fields=["is_archived", "updated_at"])
    if trip.is_archived:
        messages.success(request, "Trip archived. You can find it under “Archived”.")
        return redirect("trips:list")
    messages.success(request, "Trip restored.")
    return redirect("trips:detail", pk=trip.pk)