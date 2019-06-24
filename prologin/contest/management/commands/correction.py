# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from datetime import date

from django.core.management.base import BaseCommand

from contest.models import Contestant

from contest.models import Edition
from qcm.models import Answer


class Command(BaseCommand):
    help = "Calculate the score of the questionnary for each candidate"

    def handle(self, *args, **options):
        edition = Edition(year=date.today().year)
        contestants = Contestant.complete_for_semifinal.all().filter(edition=edition)
        nb_contestant = contestants.count()

        for i, contestant in enumerate(contestants, 1):
            answers = Answer.objects.all().filter(contestant=contestant)
            is_correct = lambda answer: answer.is_correct
            contestant.score_qualif_qcm = len(list(filter(is_correct, answers))) * 2
            print("[{}/{}] {}: {} points".format(
                i, nb_contestant, contestant.user, contestant.score_qualif_qcm
            ))
            contestant.save()


