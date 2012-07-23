# coding=utf-8
from django.db import models

# Create your models here.

class Center(models.Model):
	TYPE_CHOICES = (
		(u'c', u'centre'),
		(u'r', u'restaurant'),
		(u'h', u'hôtel'),
		(u'p', u'pizzeria'),
		(u'a', u'autre'),
	)
	ville = models.CharField(max_length = 64)
	nom = models.CharField(max_length = 64)
	type = models.CharField(max_length = 1, choices = TYPE_CHOICES)
	adresse = models.CharField(max_length = 128)
	tel = models.CharField(max_length = 10, blank = True)
	commentaires = models.TextField(blank = True)
	lat = models.DecimalField(default = '0', max_digits = 16, decimal_places = 6)
	lng = models.DecimalField(default = '0', max_digits = 16, decimal_places = 6)
