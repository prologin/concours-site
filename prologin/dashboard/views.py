import collections
import io
import json

from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.views.generic import TemplateView
from rules.compat.access_mixins import PermissionRequiredMixin

from users.models import UserActivation

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
def fetchUserActivations():
    count = UserActivation.objects.count()
    return {'name':'UserActivations','value':count,'status':count<5}

@status
def awaitingConfirmations():
    return {'name':'yolo','value':42,'status':False}

