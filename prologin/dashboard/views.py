import collections
import io
import json
import datetime

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.views.generic import TemplateView
from rules.compat.access_mixins import PermissionRequiredMixin
from django.db.models import Q

from users.models import UserActivation
from contest.models import Contestant, Edition

statusFetchers = []

class IndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'dashboard.view'
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statuses = [s() for s in statusFetchers]
        context.update({'statuses': statuses})
        return context

def status(f):
    statusFetchers.append(f)

@status
def fetchExpiredUserActivations():
    objects = UserActivation.objects.filter(
            expiration_date__lt=datetime.datetime.now())
    return {'name':'Expired user activations', 'count':objects.count(),
            'detail':objects}

@status
def fetchWeirdStates():
    # accepted in final but not in semi
    contestants = Contestant.objects.filter(Q(assignation_semifinal=0)
                                            | Q(assignation_semifinal=1),
                                            assignation_final=2)
    return {'name':'Weird states', 'count':contestants.count(),
            'detail':contestants}

