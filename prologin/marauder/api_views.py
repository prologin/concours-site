import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView, DetailView
from rules.contrib.views import PermissionRequiredMixin

import marauder.models
from marauder import gcm
from marauder.models import EventSettings, TaskForce, UserProfile
from marauder.views import MarauderMixin


class ApiGeofencesView(PermissionRequiredMixin, View):
    """API used by the Marauder app to get configured geofences."""

    permission_required = 'marauder.get-geofences'

    def get(self, request, *args, **kwargs):
        zones = []
        for event_settings in EventSettings.objects.all():
            if event_settings.is_current:
                zones.append({'lat': event_settings.lat,
                              'lon': event_settings.lon,
                              'radius_meters': event_settings.radius_meters})
        return JsonResponse({'zones': zones})


class ApiEventSettingsView(MarauderMixin, DetailView):
    """API used by the Marauder app to the event settings (location & radius)."""

    model = marauder.models.EventSettings
    permission_required = 'marauder.get-settings'

    def get_object(self, queryset=None):
        return (queryset or self.get_queryset()).get(event=self.event)

    def get(self, request, *args, **kwargs):
        settings = self.get_object()
        return JsonResponse({
            'lat': settings.lat,
            'lon': settings.lon,
            'radius': settings.radius_meters,
        })


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


@method_decorator(csrf_exempt, name='dispatch')
class ApiReportView(PermissionRequiredMixin, View):
    """API used by the Marauder app to report location changes."""

    permission_required = 'marauder.report'

    def post(self, request, *args, **kwargs):
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
            _check_taskforces_redundancy(request.current_events['final'],
                                         profile)

        return JsonResponse({})


@method_decorator(csrf_exempt, name='dispatch')
class ApiSendUserPingView(MarauderMixin, View):
    """API used by the Marauder frontend to send a ping to a single user."""

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
class ApiSendTaskforcePingView(MarauderMixin, View):
    """API used by the Marauder frontend to send a ping to a whole task force."""

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        taskforce = marauder.models.TaskForce.objects.get(pk=data['id'])
        members = taskforce.marauder_members
        if data.get('onSiteOnly', True):
            members = [member for member in members if member.online]
        gcm.multicast_notification(
            members, '[{taskforce}] {username} ({fullname})', '{reason}',
            {'taskforce': taskforce.name,
             'username': request.user.username,
             'fullname': request.user.get_full_name(),
             'reason': data['reason']})
        return HttpResponse(status=204)


class ApiTaskForcesView(MarauderMixin, ListView):
    """API used by the Marauder frontend to list the task forces & their members."""

    model = marauder.models.TaskForce
    context_object_name = 'taskforces'

    def get_queryset(self):
        return (super().get_queryset().filter(event=self.event)
                .prefetch_related('members', 'members__marauder_profile'))

    def get(self, request, *args, **kwargs):
        def members(taskforce):
            for member in (
                    taskforce.members.select_related('marauder_profile')
                    .order_by('-marauder_profile__in_area', 'username')):
                try:
                    profile = member.marauder_profile
                    online = profile.online
                except ObjectDoesNotExist:
                    profile = None
                    online = False

                yield {
                    'id': member.id,
                    'username': member.username,
                    'avatar': member.picture.url
                    if member.picture else member.avatar.url
                    if member.avatar else None,
                    'fullName': member.get_full_name(),
                    'phone': member.phone,
                    'hasDevice': profile is not None and profile.has_device,
                    'location': profile.location if profile else None,
                    'online': online,
                    'lastSeen': profile.last_seen if profile else None,
                    'lastReport': profile.last_report_seconds
                    if profile else None,
                }

        def taskforces():
            for taskforce in self.get_queryset():
                yield {
                    'id': taskforce.id,
                    'name': taskforce.name,
                    'redundancy': taskforce.redundancy,
                    'members': list(members(taskforce)),
                }

        return JsonResponse(list(taskforces()), safe=False)
