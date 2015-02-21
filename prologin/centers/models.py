from django.db import models
from prologin.utils import ChoiceEnum
import geopy.geocoders


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
    def coordinates(self):
        return "{:.6f};{:.6f}".format(self.lat, self.lng)

    @property
    def has_valid_geolocation(self):
        return self.lat != 0 and self.lng != 0

    def geocode(self, suffix=', FRANCE', geocoder=None):
        if geocoder is None:
            geocoder = geopy.geocoders.get_geocoder_for_service('google')
        location = geocoder().geocode("{name}, {addr}, {code} {city} {suffix}".format(
            name=self.name, addr=self.address, code=self.postal_code, city=self.city,
            suffix=suffix,
        ), language='fr', timeout=10)
        self.lat = location.latitude
        self.lng = location.longitude
        self.save()

    def normalize(self, suffix=', FRANCE', geocoder=None):
        if geocoder is None:
            geocoder = geopy.geocoders.get_geocoder_for_service('google')
        location = geocoder().geocode("{addr}, {code} {city} {suffix}".format(
            addr=self.address, code=self.postal_code, city=self.city,
            suffix=suffix,
        ), language='fr', timeout=10)
        addr, city, country = location.address.split(',')
        if country.strip().lower() != 'france':
            raise ValueError("Country is not France")
        code, city = city.split(None, 1)
        self.address = addr.strip()
        self.postal_code = code.strip()
        self.city = city.strip()
        self.save()

    def __str__(self):
        return self.name
