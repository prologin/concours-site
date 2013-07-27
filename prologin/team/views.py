# coding=utf-8
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.shortcuts import render, get_list_or_404
from django.core.urlresolvers import reverse
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from team.models import Team
import os

def redir(request):
    last = Team.objects.values('year').distinct().order_by('-year')[:1]
    return HttpResponseRedirect(reverse('team:year', args=(last[0]['year'],)))

def index(request, year):
    timeline = Team.objects.values('year').distinct().order_by('-year')
    year = int(year)
    team = get_list_or_404(Team.objects.order_by('role__rank'), year=year)
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
