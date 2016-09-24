from django.db import models


class School(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        if self.approved:
            return self.name
        else:
            return '(unapproved) %s' % self.name

    class Meta:
        ordering = ('approved', 'name')
