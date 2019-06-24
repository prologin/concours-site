# Copyright (C) <> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

# coding: utf-8
from django.core.management.base import BaseCommand, CommandError
from contest.models import Contest, Event, Contestant
import json

# TODO: This file is probably outdated.

def french_date(date):
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    mois = ['janvier', u'février', 'mars', 'avril', 'mai']
    return ' '.join([jours[date.weekday()], str(date.day), mois[int(date.month) - 1], str(date.year)])

class Command(BaseCommand):
    args = ''
    help = 'Test Command'
    def handle(self, *args, **options):
        prologin2013 = Contest.objects.get(year=2013)
        fail = set()
        failure = []
        success = []
        for event in prologin2013.event_set.filter(type=u'épreuve régionale'):
            fail.update([contestant for contestant in event.applicants.all() if len(contestant.events.all()) == 1])
            for contestant in event.contestant_set.all():
                center = {'date': french_date(event.begin)}
                for key in ['name', 'address', 'postal_code', 'city']:
                    center[key] = getattr(event.center, key)
                success.append({
                    'contact': {
                        'title': contestant.user.get_profile().title,
                        'first_name': contestant.user.first_name,
                        'last_name': contestant.user.last_name,
                        'email': contestant.user.email
                    },
                    'center': center
                })
        open('success.json', 'w').write(json.dumps(success, indent=4))
        for contestant in fail:
            failure.append({
                'title': contestant.user.get_profile().title,
                'first_name': contestant.user.first_name,
                'last_name': contestant.user.last_name,
                'email': contestant.user.email
            })
        open('failure.json', 'w').write(json.dumps(failure, indent=4))
