# coding=utf-8
from django.db import models

# Create your models here.

class Role(models.Model):
	rank = models.IntegerField()
	role = models.CharField(max_length = 32)
	def __unicode__(self):
		return self.role

class Team(models.Model):
	year = models.IntegerField()
	uid = models.ForeignKey('users.User')
	role = models.ForeignKey('Role')

#		(u'p', u'Président'),
#		(u'vp', u'Vice-président'),
#		(u't', u'Trésorier'),
#		(u'vt', u'Vice-trésorier'),
#		(u's', u'Secrétaire'),
#		(u'rt', u'Responsable technique'),
#		(u'm', u'Membre'),
#		(u'mp', u'Membre persistant'),
#		(u'tty', u'Mascotte'),
#		(u'c', u'Correcteur'),