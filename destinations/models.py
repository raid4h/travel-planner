from django.db import models


class Destination(models.Model):
    # TODO (after Member 1 merges the Trip model): add
    # trip = models.ForeignKey('trips.Trip', on_delete=models.CASCADE,
    #                          related_name='destinations', null=True, blank=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}, {self.country}"


class WeatherCache(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='weather')
    forecast_date = models.DateField()
    temp_max = models.FloatField()
    temp_min = models.FloatField()
    condition = models.CharField(max_length=100)
    rain_probability = models.IntegerField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('destination', 'forecast_date')
        ordering = ['forecast_date']

    def __str__(self):
        return f"{self.destination.name} {self.forecast_date}"