from collections import defaultdict

from django.conf import settings
from django.views.generic import TemplateView
from rules.compat.access_mixins import PermissionRequiredMixin
from django.db.models import Q
from django.utils import timezone

from users.models import UserActivation
from contest.models import Contestant, Edition, Assignation

statusFetchers = defaultdict(lambda: [])


class IndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'dashboard.view'
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'sections': statusFetchers})
        return context


class status(object):
    def __init__(self, category):
        self.category = category

    def __call__(self, f):
        statusFetchers[self.category].append(f)


@status("Activations")
def fetchExpiredUserActivations():
    objects = UserActivation.objects.filter(expiration_date__lt=timezone.now())
    return {
        'name': 'Expired user activations',
        'count': objects.count(),
        'detail': objects
    }


@status("Activations")
def fetchAwaitingUserActivations():
    objects = UserActivation.objects.filter(
        expiration_date__gte=timezone.now())
    return {
        'name': 'Awaiting user activations',
        'count': objects.count(),
        'detail': objects
    }


@status("Contestants")
def fetchUnassignedContestants():
    contestants = Contestant.objects.filter(
        Q(assignation_semifinal=Assignation.not_assigned.value)
        | Q(assignation_final=Assignation.not_assigned.value))
    return {
        'name': 'Unassigned contestants',
        'count': contestants.count(),
        'detail': contestants
    }


@status("Contestants")
def fetchWeirdStates():
    # accepted in final but not in semi
    contestants = Contestant.objects.filter(
        assignation_final=Assignation.assigned.value).exclude(
            assignation_semifinal=Assignation.assigned.value)
    return {
        'name': 'Weird states',
        'count': contestants.count(),
        'detail': contestants
    }


# We disable the default_factory, otherwise the template engine of django won't
# iterate over it.
statusFetchers.default_factory = None
