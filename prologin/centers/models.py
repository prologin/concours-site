from django.db import models
from django.utils.translation import ugettext_noop
import geopy.geocoders

from prologin.models import AddressableModel, ContactModel, EnumField
from prologin.utils import ChoiceEnum


class CenterQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    def active_for_prologin(self):
        return self.active().filter(for_prologin=True)
    def active_for_gcc(self):
        return self.active().filter(for_gcc=True)


class Center(AddressableModel):
    @ChoiceEnum.labels(str.capitalize)
    class Type(ChoiceEnum):
        center = 0
        restaurant = 1
        hotel = 2
        pizzeria = 3
        other = 4
        ugettext_noop("Center")
        ugettext_noop("Restaurant")
        ugettext_noop("Hotel")
        ugettext_noop("Pizzeria")
        ugettext_noop("Other")

    name = models.CharField(max_length=64)
    type = EnumField(Type)
    is_active = models.BooleanField(default=True)
    for_prologin = models.BooleanField(default=True)
    for_gcc = models.BooleanField(default=False)

    lat = models.DecimalField(default=0, max_digits=16, decimal_places=6)
    lng = models.DecimalField(default=0, max_digits=16, decimal_places=6)

    comments = models.TextField(blank=True)

    objects = CenterQuerySet.as_manager()

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


class Contact(ContactModel):
    @ChoiceEnum.labels(str.capitalize)
    class Type(ChoiceEnum):
        manager = 0
        contact = 1
        ugettext_noop("Manager")
        ugettext_noop("Contact")

    center = models.ForeignKey(Center, related_name='contacts', on_delete=models.CASCADE)
    type = EnumField(Type, db_index=True)

    def __str__(self):
        return "{} ({})".format(self.get_full_name(), Contact.Type(self.type))
