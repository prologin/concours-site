# coding=utf-8
from django.template import Context, loader
from team.models import Team
from django.http import HttpResponse
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
		if os.access('static/team/{0}.jpg'.format(member.uid.nick), os.F_OK):
			member.pic = member.uid.nick
	c = Context({
		'timeline': timeline,
		'year': year,
		'team': team,
	})
	return HttpResponse(t.render(c))
