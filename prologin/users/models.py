from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	title = models.CharField(max_length=16)
	address = models.TextField()
	postal_code = models.CharField(max_length=5)
	city = models.CharField(max_length=64)
	country = models.CharField(max_length=64)
	phone_number = models.CharField(max_length=16)
	birthday = models.DateField(max_length=64, blank=True, null=True)
	newsletter = models.BooleanField()
