from django.shortcuts import render, get_list_or_404
from team.models import TeamMember


def index(request, year=None):
    if year is None:
        year = request.current_edition.year
    team = get_list_or_404(TeamMember.objects.select_related('user', 'role'), year=year)
    return render(request, 'team/index.html', {
        'timeline': TeamMember.objects.values('year').distinct().order_by('-year'),
        'year': year,
        'team': team,
        'team_count': len(team),
    })
