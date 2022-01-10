from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from contest.models import Contestant, Event
from problems.models import Submission
from qcm.models import Qcm

class Command(BaseCommand):
    help = "Compute the scores for qualification"

    def add_arguments(self, parser):
        parser.add_argument('edition', type=int)
        parser.add_argument('--problem', action='append', type=str)
    
    def handle(self, *args, **options):
        problems = options['problem']
        edition = options['edition']
        challenge = f'qcm{edition}'
        qualif_event = None

        try:
            qualif_event = Event.objects.get(edition=edition, type=0)
        except ObjectDoesNotExist:
            raise CommandError('Failed to find qualification event (event not found)')
        except MultipleObjectsReturned:
            raise CommandError('Failed to find qualification event (multiple events)')
        
        qcm = None
        try:
            qcm = Qcm.objects.get(event=qualif_event)
        except ObjectDoesNotExist:
            raise CommandError('No QCM associated to qualification event')
        except MultipleObjectsReturned:
            raise CommandError('Multiple QCMs associated to qualification event')

        for contestant in Contestant.objects.filter(edition=edition):
            user = contestant.user
            scores = {}

            for problem in problems:
                try:
                    submission = Submission.objects.get(problem=problem, challenge=challenge, user=user)
                except ObjectDoesNotExist:
                    scores[problem] = 0
                    continue

                scores[problem] = submission.score_base
            
            scores['total_problems'] = contestant.score_qualif_algo = sum(scores.values())
            scores['total_qcm'] = contestant.score_qualif_qcm = qcm.score_for_contestant(contestant)

            print('<%s %s: %s>' % (user.first_name, user.last_name, ', '.join(f'{k}={v}' for k, v in scores.items())))
            contestant.save()