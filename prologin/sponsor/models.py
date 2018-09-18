from django.db import models

from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path


class ActiveSponsorProloginManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True,is_prologin=True)

class ActiveSponsorGccManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True,is_gcc=True)

class Sponsor(AddressableModel, ContactModel, models.Model):
    def upload_logo_to(self, *args, **kwargs):
        return upload_path('sponsor')(self, *args, **kwargs)

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_logo_to, blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_gcc = models.BooleanField(default=True)
    is_prologin = models.BooleanField(default=True)

    objects = models.Manager()
    active_prologin = ActiveSponsorProloginManager()
    active_gcc = ActiveSponsorGccManager()

    def __str__(self):
        return self.name
