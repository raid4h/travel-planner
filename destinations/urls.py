from django.urls import path, include
from rest_framework.routers import SimpleRouter

from . import views
from .api_views import DestinationViewSet

router = SimpleRouter()
router.register('api/destinations', DestinationViewSet, basename='destination')

urlpatterns = [
    path('destinations/', views.destination_page, name='destination-page'),
    path('', include(router.urls)),
]