from django.db import models
from prologin.utils import ChoiceEnum


class Center(models.Model):
    class CenterType(ChoiceEnum):
        centre = 'c'
        restaurant = 'r'
        hotel = 'h'
        pizzeria = 'p'
        autre = 'a'

    name = models.CharField(max_length=64)
    type = models.CharField(max_length=1, choices=CenterType.choices())
    is_active = models.BooleanField(default=True)

    address = models.CharField(max_length=256)
    postal_code = models.CharField(max_length=5)
    city = models.CharField(max_length=64)
    lat = models.DecimalField(default=0, max_digits=16, decimal_places=6)
    lng = models.DecimalField(default=0, max_digits=16, decimal_places=6)

    phone_number = models.CharField(max_length=10, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ('type', 'name', 'city',)

    @property
    def has_valid_geolocation(self):
        return self.lat != 0 and self.lng != 0

    def __str__(self):
        return self.name
