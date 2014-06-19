from django.shortcuts import render, get_list_or_404
from team.models import TeamMember

def index(request, year):
    team = get_list_or_404(TeamMember.objects.order_by('role__rank'), year=year)
    return render(request, 'team/index.html', {
        'timeline': TeamMember.objects.values('year').distinct().order_by('-year'),
        'year': year,
        'team': team,
    })
