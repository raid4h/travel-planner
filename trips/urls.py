# =====================================================================
# File: trips/urls.py
# Purpose: The web addresses (URLs) that belong to the trips app.
#          config/urls.py includes this file.
# Contains:
#   /trips/                    -> My Trips list      (trips:list)
#   /trips/new/                -> create a trip      (trips:create)
#   /trips/<id>/               -> trip details       (trips:detail)
#   /trips/<id>/edit/          -> edit a trip        (trips:edit)
#   /trips/<id>/delete/        -> delete (confirm)   (trips:delete)
#   /trips/<id>/archive/       -> archive/restore    (trips:archive)
# =====================================================================

from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("trips/", views.TripListView.as_view(), name="list"),
    path("trips/new/", views.TripCreateView.as_view(), name="create"),
    path("trips/<int:pk>/", views.TripDetailView.as_view(), name="detail"),
    path("trips/<int:pk>/edit/", views.TripUpdateView.as_view(), name="edit"),
    path("trips/<int:pk>/delete/", views.TripDeleteView.as_view(), name="delete"),
    path("trips/<int:pk>/archive/", views.toggle_archive, name="archive"),
]