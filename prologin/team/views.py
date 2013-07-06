# coding=utf-8
from django.template import Context, loader
from team.models import Team
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
import os

def index(request, year=None):
    timeline = Team.objects.values('year').distinct().order_by('-year')
    if not year:
        year = max([int(team['year']) for team in timeline])
    year = int(year)
    team = Team.objects.filter(year=year).order_by('role')
    for member in team:
        member.pic = 'unknown'
        absolute_path = finders.find('team/{0}.jpg'.format(member.user.username))
        if staticfiles_storage.exists(absolute_path):
            member.pic = member.user.username
    c = RequestContext(request, {
        'timeline': timeline,
        'year': year,
        'team': team,
    })
    return render(request, 'team/index.html', c)
