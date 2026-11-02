from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from trips.models import Trip
from .models import AIPlan
from .serializers import AIPlanSerializer
from .ai.services import generate_and_save_itinerary


# 1. Show all AI itineraries of the logged-in user
class AIPlanListCreateView(generics.ListAPIView):
    serializer_class = AIPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIPlan.objects.filter(
            trip__owner=self.request.user
        ).prefetch_related("items")


# 2. Show details of a specific AI itinerary
class AIPlanDetailView(generics.RetrieveAPIView):
    serializer_class = AIPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIPlan.objects.filter(
            trip__owner=self.request.user
        ).prefetch_related("items")


# 3. Generate and save AI itinerary
class GenerateItineraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        trip_id = request.data.get("trip_id")

        if not trip_id:
            return Response(
                {"error": "trip_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        trip = get_object_or_404(
            Trip,
            id=trip_id,
            owner=request.user
        )

        try:
            ai_plan = generate_and_save_itinerary(trip)
            serializer = AIPlanSerializer(ai_plan)

            return Response(
                {
                    "message": "Itinerary generated and saved successfully.",
                    "plan": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except Exception:
            return Response(
                {
                    "error": "Something went wrong while generating itinerary."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# 4. Display the AI Itinerary Planner frontend page
@login_required
def planner_page(request):

    trips = Trip.objects.filter(
        owner=request.user,
        is_archived=False
    )

    return render(
        request,
        "itinerary/planner.html",
        {"trips": trips}
    )

