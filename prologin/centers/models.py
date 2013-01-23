# coding=utf-8
from django.db import models

class Center(models.Model):
    TYPE_CHOICES = (
        (u'c', u'centre'),
        (u'r', u'restaurant'),
        (u'h', u'hôtel'),
        (u'p', u'pizzeria'),
        (u'a', u'autre'),
    )
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    address = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=5)
    city = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=10, blank=True)
    comments = models.TextField(blank=True)
    lat = models.DecimalField(default='0', max_digits=16, decimal_places=6)
    lng = models.DecimalField(default='0', max_digits=16, decimal_places=6)
    is_active = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
