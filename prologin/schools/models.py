from django.conf import settings
from django.db import models


class School(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)

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
