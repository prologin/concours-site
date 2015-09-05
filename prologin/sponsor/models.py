from django.db import models

from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path


class Sponsor(AddressableModel, ContactModel):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_path('sponsor'), blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    editions = models.ManyToManyField('contest.Edition', blank=True)

    def __str__(self):
        return self.name
