from django.db import models

from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path

RANK_CHOICES = (
    ("gold", "Gold"),
    ("silver", "Silver"),
    ("bronze", "Bronze")
)


class ActiveSponsorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Sponsor(AddressableModel, ContactModel, models.Model):
    def upload_logo_to(self, *args, **kwargs):
        return upload_path('sponsor')(self, *args, **kwargs)

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_logo_to, blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    rank = models.CharField(
            choices=RANK_CHOICES,
            max_length=20,
            blank=True
    )
    objects = models.Manager()
    active = ActiveSponsorManager()

    def __str__(self):
        return self.name
