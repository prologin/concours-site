from collections import defaultdict
from textwrap import dedent

from django.conf import settings
from django.views.generic import TemplateView
from rules.compat.access_mixins import PermissionRequiredMixin
from django.db.models import Q
from django.utils import timezone

from users.models import UserActivation
from contest.models import Contestant, Edition, Assignation


class IndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'dashboard.view'
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sections = defaultdict(list)

        for subclass in Status.__subclasses__():
            inst = subclass()
            sections[subclass.category].append(inst)

        sections.default_factory = None
        context.update({'sections': sections})
        return context


class Status():
    category = None
    name = None
    count = None
    detail = None

    def __init__(self):
        pass

    def md(self):
        """
        Quickly format the docstring so the <pre> tag does not show the first
        indent.
        """
        return dedent(self.__doc__)


class ExpiredUserActivations(Status):
    """
    The list of expired UserActivation objects.

    These objects eat up space without any use.

    To remove them you could use the following django query:
    
    ```python
    UserActivation.objects.filter(
            expiration_date__lt=timezone.now()).delete()
    ```
    """
    category = "Activations"
    name = "Expired user activations"

    def __init__(self):
        super().__init__()
        objects = UserActivation.objects.filter(
            expiration_date__lt=timezone.now())
        self.count = objects.count()
        self.detail = objects


class UnassignedContestants(Status):
    """
    The list of unassigned contestants.

    You should fix this by assigning the contestants in the correction admin
    page.
    """
    category = "Contestants"
    name = "Unassigned contestants"

    def __init__(self):
        super().__init__()
        contestants = Contestant.objects.filter(
            Q(assignation_semifinal=Assignation.not_assigned.value)
            | Q(assignation_final=Assignation.not_assigned.value))
        self.count = contestants.count()
        self.detail = contestants


class WeirdContestantStates(Status):
    """
    The list of contestants in a weird states.

    These are contestants that are accepted in final, but not assigned in semi.

    You should try to find why this happened before removing them with the
    following query:
    
    ```python
    Contestant.objects.filter(
            assignation_final=Assignation.assigned.value).exclude(
            assignation_semifinal=Assignation.assigned.value)
    ```
    """
    category = "Contestants"
    name = "Weird contestant states"

    def __init__(self):
        contestants = Contestant.objects.filter(
            assignation_final=Assignation.assigned.value).exclude(
                assignation_semifinal=Assignation.assigned.value)
        self.count = contestants.count()
        self.detail = contestants
