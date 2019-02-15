from django.db import models

from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path


class SponsorQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    def active_for_prologin(self):
        return self.active().filter(for_prologin=True)
    def active_for_gcc(self):
        return self.active().filter(for_gcc=True)


class Sponsor(AddressableModel, ContactModel, models.Model):
    def upload_logo_to(self, *args, **kwargs):
        return upload_path('sponsor')(self, *args, **kwargs)

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_logo_to, blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    for_gcc = models.BooleanField(default=True)
    for_prologin = models.BooleanField(default=True)

    objects = SponsorQuerySet.as_manager()

    def __str__(self):
        return self.name
