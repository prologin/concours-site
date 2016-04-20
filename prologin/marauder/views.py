from django.core.exceptions import ObjectDoesNotExist
from django.http.response import JsonResponse
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin, TemplateView
from django.views.generic.list import ListView

import prologin.utils
import marauder.models


class MarauderMixin(ContextMixin):
    @cached_property
    def event(self):
        return self.request.current_events['final']

    def get_context_data(self, **kwargs):
        kwargs['event'] = self.event
        return super().get_context_data(**kwargs)


class ApiTaskForcesView(prologin.utils.LoginRequiredMixin, MarauderMixin, ListView):
    model = marauder.models.TaskForce
    context_object_name = 'taskforces'

    def get_queryset(self):
        return (super().get_queryset()
                .filter(event=self.event)
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
                'avatar': member.picture.url if member.picture else member.avatar.url if member.avatar else None,
                'fullName': member.get_full_name(),
                'lastSeen': profile(member, lambda p: int(p.location_timestamp.timestamp()) if p.location_timestamp else None),
                'online': profile(member, lambda p: p.in_area),
                'phone': member.phone,
            } for member in taskforce.members.select_related('marauder_profile').all()]
        } for taskforce in self.get_queryset()]
        return JsonResponse(items, safe=False)


class IndexView(prologin.utils.LoginRequiredMixin, MarauderMixin, TemplateView):
    template_name = 'marauder/index.html'
