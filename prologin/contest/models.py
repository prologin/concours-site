# -*- coding: utf8 -*-
from django.db import models
from centers.models import Center
from django.contrib.auth.models import User

class Contest(models.Model):
	year = models.IntegerField()
	def __unicode__(self):
		return str(self.year)

class Event(models.Model):
	EVENT_TYPES = (
		('questionnaire', 'questionnaire'),
		(u'épreuve régionale', u'épreuve régionale'),
		('finale', 'finale'),
	)
	contest = models.ForeignKey(Contest)
	center = models.ForeignKey(Center)
	type = models.CharField(max_length=17, choices=EVENT_TYPES)
	begin = models.DateTimeField(blank=True, null=True)
	end = models.DateTimeField(blank=True, null=True)
	def __unicode__(self):
		return u'Prologin {0} - {1}'.format(self.contest.year, self.center)

class Contestant(models.Model):
	user = models.ForeignKey(User)
	event_choices = models.ManyToManyField(Event, related_name='applicants')
	events = models.ManyToManyField(Event)
	def year(self):
		return '{0}'.format(self.events.all()[0].contest.year)

class Score(models.Model):
	SCORE_TYPES = (
		('written', 'written'),
		('interview', 'interview'),
		('machine', 'machine'),
	)
	contestant = models.ForeignKey(Contestant)
	type = models.CharField(max_length=42, choices=SCORE_TYPES)
	score = models.IntegerField()
