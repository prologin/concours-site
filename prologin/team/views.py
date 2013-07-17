# coding=utf-8
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext, Context, loader
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from team.models import Team
import os

def redir(request, year=None):
    last = Team.objects.values('year').distinct().order_by('-year')[:1]
    return HttpResponseRedirect(reverse('team:team_year', args=(last[0]['year'],)))

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
