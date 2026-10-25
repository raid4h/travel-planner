from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_dashboard_chart_data, get_dashboard_overview


class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_param = request.query_params.get("trip")
        trip_id = int(trip_param) if trip_param and trip_param.isdigit() else None

        overview = get_dashboard_overview(request.user)
        charts = get_dashboard_chart_data(request.user, trip_id=trip_id)
        stats = overview["stats"]

        return Response(
            {
                "stats": {
                    "total_trips": stats["total_trips"],
                    "ongoing_count": stats["ongoing_count"],
                    "upcoming_count": stats["upcoming_count"],
                    "completed_count": stats["completed_count"],
                    "total_budget": str(stats["total_budget"]),
                    "total_spent": str(stats["total_spent"]),
                    "total_remaining": str(stats["total_remaining"]),
                    "is_over_budget": stats["is_over_budget"],
                },
                "charts": charts,
            }
        )

