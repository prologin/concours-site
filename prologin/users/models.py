from django.db import models

# Create your models here.

class User(models.Model):
	nick = models.CharField(max_length = 64)
	titre = models.CharField(max_length = 16)
	prenom = models.CharField(max_length = 64)
	nom = models.CharField(max_length = 64)
	adresse = models.TextField()
	code_postal = models.CharField(max_length = 5)
	ville = models.CharField(max_length = 64)
	number = models.CharField(max_length = 16)
	niveau = models.CharField(max_length = 32)
	birthday = models.CharField(max_length = 64)
	newsletter = models.BooleanField()
	def __unicode__(self):
		return u'{0} {1} ({2})'.format(self.prenom, self.nom, self.nick)
