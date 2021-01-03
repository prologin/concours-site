from oidc_provider.lib.claims import ScopeClaims
from contest.models import Contestant
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

class ProloginScopeClaims(ScopeClaims):

    info_contest = (
        'Candidature au Concours Prologin',
        'Informations relevant du concours Prologin'
    )

    def scope_contest(self):
        contest_is_contestant = False
        cont = None

        try:
            cont = Contestant.objects.get(
                edition=settings.PROLOGIN_EDITION,
                user=self.user,
            )
            contest_is_contestant = True
        except ObjectDoesNotExist:
            contest_is_contestant = False
            cont = None

        dic = {
            'is_contestant': contest_is_contestant,
        }

        if contest_is_contestant:
            dic['contestant'] = {
                'assignation_semifinal': cont.assignation_semifinal,
                'assignation_final': cont.assignation_final,
            }

            if cont.assignation_semifinal_event != None:
                dic['contestant']['assignation_semifinal_event'] = {
                    'id': cont.assignation_semifinal_event.pk,
                    'center_name': cont.assignation_semifinal_event.center.name,
                }

        return dic

    info_security_clearance = (
        'Informations d\'autorisation',
        'Groupes de sécurité, statut staff / super-utilisateur'
    )

    def scope_security_clearance(self):
        dic = {
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'groups': [
                {
                    'name': group.name,
                    'id': group.pk,
                } for group in self.user.groups.all()
            ],
        }

        return dic
