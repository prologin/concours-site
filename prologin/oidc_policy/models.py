from contest.models import Contestant

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models

class OpenIDClientPolicy(models.Model):
    openid_client = models.OneToOneField(to='oidc_provider.Client', on_delete=models.CASCADE, primary_key=True)
    allow_groups = models.ManyToManyField(
        to=Group,
        blank=True,
        help_text='If not blank, represents the groups allowed to login through this client.')
    allow_staff = models.BooleanField(help_text='Allow staff users to login through this client.', default=False)
    allow_assigned_semifinal = models.BooleanField(
        help_text='Allow contestants of the current edition assigned to semifinal to login through this client.',
        default=False,
    )
    allow_assigned_semifinal_event = models.ForeignKey(
        to='contest.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Allow contestants of the current edition assigned to the selected semifinal event to login through this client.',
        limit_choices_to={'type': 1, 'edition': settings.PROLOGIN_EDITION},
    )
    allow_assigned_final = models.BooleanField(
        help_text='Allow contestants of the current edition assigned to final to login through this client.',
        default=False,
    )

    class Meta:
        verbose_name = 'OpenID Client Policy'
        verbose_name_plural = 'OpenID Client Policies'

    def __str__(self):
        return self.openid_client.name

    def is_user_allowed(self, user):
        """
        this function takes an instance of ProloginUser as argument
        and returns True if user is allowed to use the client or
        False if the user is not allowed to use the client
        """
        if (
                user.is_superuser or
                (self.allow_staff and user.is_staff) or
                user.groups.filter(pk__in=self.allow_groups.all())
            ):
            return True

        contestant = None
        try:
            contestant = Contestant.objects.get(edition=settings.PROLOGIN_EDITION, user=user)
        except ObjectDoesNotExist:
            return False

        if (
                (self.allow_assigned_semifinal and contestant.assignation_semifinal == 2) or
                (self.allow_assigned_final and contestant.assignation_final == 2) or
                (self.allow_assigned_semifinal_event == contestant.assignation_semifinal_event != None)
            ):
            return True

        return False
