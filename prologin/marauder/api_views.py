import json

import traceback
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView

import marauder.models
import team.models
import prologin.utils
from marauder import gcm
from marauder.models import EventSettings, UserProfile
from marauder.views import MarauderMixin


def geofences(request):
    """API used by the Marauder app to get configured geofences."""
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
            profile.last_within_timestamp = timezone.now()
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


class ApiTaskForcesView(prologin.utils.LoginRequiredMixin, MarauderMixin,
                        ListView):
    model = marauder.models.TaskForce
    context_object_name = 'taskforces'

    def get_queryset(self):
        return (super().get_queryset().filter(event=self.event)
                .prefetch_related('members', 'members__marauder_profile'))

    def get(self, request, *args, **kwargs):
        def profile(member, func):
            try:
                return func(member.marauder_profile)
            except ObjectDoesNotExist:
                return None

        items = [{
            'id': taskforce.id,
            'name': taskforce.name,
            'members': [{
                'id': member.id,
                'username': member.username,
                'avatar': member.picture.url if member.picture else
                member.avatar.url if member.avatar else None,
                'fullName': member.get_full_name(),
                'lastSeen': profile(
                    member,
                    lambda p: int(p.last_report_timestamp.timestamp()) if p.last_report_timestamp else None),
                'online': profile(member, lambda p: p.in_area),
                'hasDevice': profile(member, lambda p: bool(p.gcm_token)),
                'phone': member.phone,
            }
                        for member in taskforce.members.select_related(
                            'marauder_profile').all()]
        } for taskforce in self.get_queryset()]
        return JsonResponse(items, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class ApiSendUserPingView(prologin.utils.LoginRequiredMixin, MarauderMixin,
                          View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        recipient = marauder.models.UserProfile.objects.get(
            user__pk=data['id'])
        gcm.unicast_notification(recipient, '{username} ({fullname})',
                                 '{reason}',
                                 {'username': request.user.username,
                                  'fullname': request.user.get_full_name(),
                                  'reason': data['reason']})
        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
class ApiSendTaskforcePingView(prologin.utils.LoginRequiredMixin,
                               MarauderMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        taskforce = marauder.models.TaskForce.objects.get(pk=data['id'])
        gcm.multicast_notification(taskforce.marauder_members,
                                   '[{taskforce}] {username} ({fullname})',
                                   '{reason}',
                                   {'taskforce': taskforce.name,
                                    'username': request.user.username,
                                    'fullname': request.user.get_full_name(),
                                    'reason': data['reason']})
        return HttpResponse(status=204)
