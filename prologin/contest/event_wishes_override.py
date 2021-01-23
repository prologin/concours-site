from django.contrib.auth.mixins import PermissionRequiredMixin
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import contest.models
import pytz

def get_wish_override_context(contestant):
    context = {
        'allowed': contestant_can_override_wish(contestant),
        'allowed_until': may_override_until(),
    }

    if context['allowed']:
        context['first_wish'] = contestant.assignation_semifinal_wishes.first()

    return context

def may_override_until():
    return getattr(settings, "PROLOGIN_WISHES_OVERRIDE_UNTIL", datetime(1999, 1, 1, tzinfo=pytz.UTC))


def contestant_can_override_wish(contestant):
    return (
        contestant.assignation_semifinal == contest.models.Assignation.not_assigned.value
        and timezone.now() <= may_override_until()
    )

class CanOverrideEventWishMixin(PermissionRequiredMixin):

    def has_permission(self):
        return self.request.user.is_authenticated and contestant_can_override_wish(self.request.current_data.current_contestant)
