import json

import traceback
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView

import marauder.models
import team.models
import prologin.utils
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
                    lambda p: int(p.location_timestamp.timestamp()) if p.location_timestamp else None),
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
        try:
            data = json.loads(request.body.decode())
            recipient = marauder.models.UserProfile.objects.get(
                user__pk=data['id']).gcm_token
            marauder.models.gcm_send(recipient,
                                     {
                                         'title': "{} ({})".format(
                                             request.user.username,
                                             request.user.get_full_name()),
                                         'message': data['reason'],
                                     },
                                     timeout=2)
            return HttpResponse(status=204)
        except Exception:
            pass
        return HttpResponseBadRequest()


@method_decorator(csrf_exempt, name='dispatch')
class ApiSendTaskforcePingView(prologin.utils.LoginRequiredMixin,
                               MarauderMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode())
            taskforce = marauder.models.TaskForce.objects.get(pk=data['id'])
            recipients = (taskforce.members.select_related('marauder_profile')
                          .exclude(marauder_profile__gcm_token='')
                          .exclude(marauder_profile__gcm_token__isnull=True)
                          .values_list('marauder_profile__gcm_token',
                                       flat=True))
            print(recipients)
            message = {
                'title': "[{}] {} ({})".format(taskforce.name,
                                               request.user.username,
                                               request.user.get_full_name()),
                'message': data['reason'],
            }
            for recipient in recipients:
                # FIXME: may be burst rate-limited
                marauder.models.gcm_send(recipient, message, timeout=2)
            return HttpResponse(status=204)
        except Exception:
            pass
        return HttpResponseBadRequest()
