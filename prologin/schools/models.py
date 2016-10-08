from django.conf import settings
from django.db import models

from prologin.models import AddressableModel


class School(AddressableModel):
    name = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)

    # Optional fields
    imported = models.BooleanField(default=False, blank=False, null=False)
    uai = models.CharField(max_length=16, blank=True, null=True, db_index=True,
                           unique=True)
    acronym = models.CharField(max_length=32, blank=True, null=True)
    type = models.CharField(max_length=128, blank=True, null=True)
    academy = models.CharField(max_length=128, blank=True, null=True)

    def edition_contestants(self, year):
        return self.contestants.filter(edition__year=year)

    @property
    def current_edition_contestants(self):
        return self.edition_contestants(settings.PROLOGIN_EDITION)

    @property
    def total_contestants_count(self):
        return self.contestants.count()

    @property
    def current_edition_contestants_count(self):
        return self.current_edition_contestants.count()

    def __str__(self):
        if self.approved:
            return self.name
        else:
            return '(unapproved) %s' % self.name

    class Meta:
        ordering = ('approved', 'name')
