from django.contrib import admin
from .models import Destination, WeatherCache

admin.site.register(Destination)
admin.site.register(WeatherCache)