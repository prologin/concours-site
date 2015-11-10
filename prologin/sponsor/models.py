from adminsortable.models import SortableMixin
from django.db import models

from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path


class ActiveSponsorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Sponsor(SortableMixin, AddressableModel, ContactModel):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_path('sponsor'), blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    editions = models.ManyToManyField('contest.Edition', blank=True, related_name='sponsors')
    order = models.SmallIntegerField(default=0, editable=False, db_index=True)

    objects = models.Manager()
    active = ActiveSponsorManager()

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.name
