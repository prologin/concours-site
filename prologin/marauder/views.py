from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse

from marauder.models import UserProfile

import json
import team.models

@csrf_exempt
def report(request):
    """API used by the background service of the Marauder app."""
    if request.method != 'POST':
        return HttpResponseBadRequest()

    if not request.user.is_authenticated():
        return HttpResponseForbidden()
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
