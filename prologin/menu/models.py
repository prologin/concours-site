from django.db import models

class MenuEntry(models.Model):
    name = models.CharField(max_length=32)
    url = models.CharField(max_length=120) # Do not change me to an URLField, I wouldn't be able to store relative URLs!
    parent = models.ForeignKey('self', null=True, blank=True, default=None)
    position = models.IntegerField()
    access_types = (
        ('all', 'All'),
        ('guest', 'Guest only'),
        ('logged', 'Logged users'),
        ('admin', 'Admin'),
    )
    access = models.CharField(max_length=10, choices=access_types, default='all')

    def __str__(self):
        return self.name.encode('utf-8')

    class Meta:
        verbose_name = 'Menu entry'
        verbose_name_plural = 'Menu entries'
