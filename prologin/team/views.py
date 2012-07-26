# coding=utf-8
from django.template import Context, loader
from team.models import Team
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
import os

def list_team(request, year=None):
	timeline = Team.objects.values('year').distinct().order_by('-year')
	if not year:
		year = max([int(team['year']) for team in timeline])
	year = int(year)
	t = loader.get_template('team/index.html')
	team = Team.objects.filter(year=year).order_by('role')
	for member in team:
		member.pic = 'unknown'
		absolute_path = finders.find('team/{}.jpg'.format(member.user.username))
		if staticfiles_storage.exists(absolute_path):
			member.pic = member.user.username
	c = Context({
		'timeline': timeline,
		'year': year,
		'team': team,
	})
	return HttpResponse(t.render(c))
