from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Destination
from .serializers import DestinationSerializer, WeatherSerializer
from .services.geocoding import search_places, GeocodingError
from .services.weather import get_forecast, WeatherError


class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all().order_by('-created_at')
    serializer_class = DestinationSerializer
    # TODO: change to IsAuthenticated once Member 1's login is merged
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'detail': 'Enter at least 2 characters.'}, status=400)
        try:
            return Response(search_places(q))
        except GeocodingError as exc:
            return Response({'detail': str(exc)}, status=502)

    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        destination = self.get_object()
        try:
            forecast = get_forecast(destination)
        except WeatherError as exc:
            return Response({'detail': str(exc)}, status=502)
        return Response(WeatherSerializer(forecast, many=True).data)