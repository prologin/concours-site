from django.db import models
from django.utils.translation import ugettext_lazy as _
from prologin.utils import upload_path
import contest.models


class AddressableModel(models.Model):
    address = models.TextField(blank=True, verbose_name=_("N° et voie"))
    postal_code = models.CharField(max_length=5, blank=True, verbose_name=_("Code postal"))
    city = models.CharField(max_length=64, blank=True, verbose_name=_("Ville"))
    country = models.CharField(max_length=64, blank=True, verbose_name=_("Pays"))

    class Meta:
        abstract = True


class Sponsor(AddressableModel):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_path('sponsor'), blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    editions = models.ManyToManyField(contest.models.Edition, blank=True)

    email = models.EmailField(blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    phone_desk = models.CharField(max_length=64, blank=True)
    phone_mobile = models.CharField(max_length=64, blank=True)
    phone_contact = models.CharField(max_length=64, blank=True)
    phone_fax = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.name
