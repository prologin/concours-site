# coding=utf8
from django.core.management.base import BaseCommand, CommandError
from contest.models import Contest, Event, Contestant
from datetime import date

class Command(BaseCommand):
    args = ''
    help = 'Test Command'
    def handle(self, *args, **options):
        prologin2013 = Contest.objects.get(year=2013)
        success = []
        for event in prologin2013.event_set.filter(type=u'épreuve régionale'):
            for contestant in event.contestant_set.all():
                if contestant.user.get_profile().birthday < date(1992, 1, 1) or contestant.user.get_profile().birthday > date(2002, 1, 1):
                    print u'%s %s (%s) est né le %s' % (contestant.user.first_name, contestant.user.last_name, contestant.user.email, str(contestant.user.get_profile().birthday))
