import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

import team.models
from marauder.models import EventSettings, UserProfile


def geofences(request):
    """API used by the Marauder app to get configured geofences."""
    if not team.models.TeamMember.objects.filter(user=request.user):
        return HttpResponseForbidden()

    zones = []
    for event_settings in EventSettings.objects.all():
        if event_settings.is_current:
            zones.append({'lat': event_settings.lat,
                          'lon': event_settings.lon,
                          'radius_meters': event_settings.radius_meters})
    return JsonResponse({'zones': zones})


@login_required
@csrf_exempt
def report(request):
    """API used by the Marauder app to report location changes."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    if not team.models.TeamMember.objects.filter(user=request.user):
        return HttpResponseForbidden()

    profile = getattr(request.user, 'marauder_profile', UserProfile())
    profile.user = request.user

    if request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return HttpResponseBadRequest()
        if data.get('in_area'):
            profile.in_area = True
            profile.lat = data['lat']
            profile.lon = data['lon']
        else:
            profile.in_area = False
            profile.lat = profile.lon = 0
        if 'gcm' in data:
            profile.gcm_app_id = data['gcm']['app_id']
            profile.gcm_token = data['gcm']['token']

    profile.save()
    return JsonResponse({})
