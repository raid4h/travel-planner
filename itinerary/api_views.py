from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from trips.models import Trip
from .models import AIPlan
from .serializers import AIPlanSerializer
from .ai.services import generate_and_save_itinerary


class AIPlanListCreateView(generics.ListAPIView):
    serializer_class = AIPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIPlan.objects.filter(
            trip__owner=self.request.user
        ).prefetch_related("items")


class AIPlanDetailView(generics.RetrieveAPIView):
    serializer_class = AIPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIPlan.objects.filter(
            trip__owner=self.request.user
        ).prefetch_related("items")


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
                {"error": "Something went wrong while generating itinerary."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


