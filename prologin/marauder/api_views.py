import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView, DetailView

import marauder.models
import team.models
import prologin.utils
from marauder import gcm
from marauder.models import EventSettings, TaskForce, UserProfile
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
    in_area_transition = False

    if request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except ValueError:
            return HttpResponseBadRequest()
        in_area_transition = bool(data.get('in_area')) != profile.in_area
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

    if in_area_transition:
        _check_taskforces_redundancy(request.current_events['final'], profile)

    return JsonResponse({})


def _check_taskforces_redundancy(event, moved_profile):
    """
    Checks whether Task Forces still have the required redundancy, and send
    notifications when they don't.
    """
    for taskforce in TaskForce.objects.filter(
            event=event,
            members__marauder_profile=moved_profile).prefetch_related(
                'members', 'members__marauder_profile'):
        if taskforce.redundancy == 0:
            continue

        other_members_on_site = [
            profile
            for profile in taskforce.marauder_members
            if profile.in_area and profile != moved_profile
        ]
        if moved_profile.in_area:  # Entering area.
            if len(other_members_on_site) <= taskforce.redundancy:
                gcm.multicast_notification(
                    other_members_on_site + [moved_profile],
                    '{taskforce} redundancy change',
                    '{moved_user} just arrived. Now {present} people present '
                    '(of {needed} required).',
                    {'taskforce': taskforce.name,
                     'moved_user': moved_profile.user.username,
                     'present': len(other_members_on_site) + 1,
                     'needed': taskforce.redundancy})
        else:  # Leaving area.
            if len(other_members_on_site) == taskforce.redundancy:
                gcm.multicast_notification(
                    other_members_on_site, '{taskforce} at redundancy limit',
                    '{moved_user} just left. Now {present} people present '
                    '(of {needed} required), avoid leaving.',
                    {'taskforce': taskforce.name,
                     'moved_user': moved_profile.user.username,
                     'present': len(other_members_on_site),
                     'needed': taskforce.redundancy})
            elif len(other_members_on_site) < taskforce.redundancy:
                gcm.multicast_notification(
                    other_members_on_site,
                    '{taskforce} below redundancy limit',
                    '{moved_user} just left. Now {present} people present '
                    '(of {needed} required), avoid leaving.',
                    {'taskforce': taskforce.name,
                     'moved_user': moved_profile.user.username,
                     'present': len(other_members_on_site),
                     'needed': taskforce.redundancy})
                gcm.unicast_notification(
                    moved_profile, '{taskforce} redundancy problem',
                    'You just left while {taskforce} is at or below '
                    'redundancy limit ({present} of {needed} required). '
                    'Try to be back soon or seek coverage.',
                    {'taskforce': taskforce.name,
                     'present': len(other_members_on_site),
                     'needed': taskforce.redundancy})


class ApiEventSettingsView(prologin.utils.LoginRequiredMixin, MarauderMixin,
                           DetailView):
    model = marauder.models.EventSettings

    def get_object(self, queryset=None):
        return (queryset or self.get_queryset()).get(event=self.event)

    def get(self, request, *args, **kwargs):
        settings = self.get_object()
        return JsonResponse({
            'lat': settings.lat,
            'lon': settings.lon,
            'radius': settings.radius_meters,
        })


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
            'redundancy': taskforce.redundancy,
            'members': [{
                'id': member.id,
                'username': member.username,
                'avatar': member.picture.url if member.picture else
                member.avatar.url if member.avatar else None,
                'fullName': member.get_full_name(),
                'lastSeen': profile(
                    member,
                    lambda p: int(p.last_within_timestamp.timestamp()) if p.last_within_timestamp else None),
                'lastReport': profile(
                    member,
                    lambda p: (timezone.now() - p.last_report_timestamp).seconds if p.last_report_timestamp else None),
                'location': profile(member, lambda p: {'lat': p.lat, 'lon': p.lon}),
                'online': profile(member, lambda p: p.in_area),
                'hasDevice': profile(member, lambda p: bool(p.gcm_token)),
                'phone': member.phone,
            }
                        for member in taskforce.members.select_related(
                            'marauder_profile').order_by('-marauder_profile__in_area', 'username')]
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
