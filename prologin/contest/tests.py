# Copyright (C) <2012> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import unittest.mock
from datetime import datetime, timedelta

from django.utils.timezone import make_aware

from contest.models import Edition, Event, Contestant, Assignation
from users.models import ProloginUser
from prologin.tests import ProloginTestCase


def mock_dt(datetime):
    def mocked_now():
        return make_aware(datetime)

    def decorator(func):
        return unittest.mock.patch('django.utils.timezone.now', new=mocked_now)(func)

    return decorator


class EventPhaseTest(ProloginTestCase):
    def setUp(self):
        self.edition = Edition.objects.create(year=2016,
                                              date_begin=make_aware(datetime(2015, 8, 25)),
                                              date_end=make_aware(datetime(2016, 5, 30)))
        self.edition.save()
        qualif = Event.objects.create(edition=self.edition,
                                      type=Event.Type.qualification.value,
                                      date_begin=make_aware(datetime(2015, 9, 1)),
                                      date_end=make_aware(datetime(2016, 1, 1)))
        qualif.save()
        semi1 = Event.objects.create(edition=self.edition,
                                     type=Event.Type.semifinal.value,
                                     date_begin=make_aware(datetime(2016, 2, 1)),
                                     date_end=make_aware(datetime(2016, 2, 2)))
        semi1.save()
        semi2 = Event.objects.create(edition=self.edition,
                                     type=Event.Type.semifinal.value,
                                     date_begin=make_aware(datetime(2016, 3, 1)),
                                     date_end=make_aware(datetime(2016, 3, 2)))
        semi2.save()
        semi3 = Event.objects.create(edition=self.edition,
                                     type=Event.Type.semifinal.value,
                                     date_begin=make_aware(datetime(2016, 4, 1)),
                                     date_end=make_aware(datetime(2016, 4, 2)))
        semi3.save()
        final = Event.objects.create(edition=self.edition,
                                     type=Event.Type.final.value,
                                     date_begin=make_aware(datetime(2016, 5, 20)),
                                     date_end=make_aware(datetime(2016, 5, 23)))
        final.save()
        self.noob_user = ProloginUser(username='noob', email='noob@example.org')
        self.noob_user.save()
        self.noob_contestant = Contestant(
            user=self.noob_user, edition=self.edition, assignation_semifinal=Assignation.ruled_out.value)
        self.noob_contestant.save()
        self.semifinal_user = ProloginUser(username='goes-to-semifinal', email='semifinal@example.org')
        self.semifinal_user.save()
        self.semifinal_contestant = Contestant(
            user=self.semifinal_user, edition=self.edition,
            assignation_semifinal=Assignation.assigned.value, assignation_final=Assignation.ruled_out.value)
        self.semifinal_contestant.save()
        self.final_user = ProloginUser(username='goes-to-final', email='final@example.org')
        self.final_user.save()
        self.final_contestant = Contestant(
            user=self.final_user, edition=self.edition,
            assignation_semifinal=Assignation.assigned.value, assignation_final=Assignation.assigned.value)
        self.final_contestant.save()

    def tearDown(self):
        Edition.objects.all().delete()

    def assertPhaseIs(self, event, type):
        current_event, current_type = self.edition.phase
        self.assertEqual(current_event, event)
        self.assertEqual(current_type, type)

    def assertCanEdit(self, *users):
        for user in users:
            self.assertTrue(user.can_edit_profile(self.edition), "{} can NOT edit profile, but should".format(user))

    def assertCanNotEdit(self, *users):
        for user in users:
            self.assertFalse(user.can_edit_profile(self.edition), "{} CAN edit profile, but shouldn't".format(user))

    @mock_dt(datetime(2015, 8, 1))
    def test_edition_before_begin(self):
        self.assertPhaseIs(None, 'future')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2015, 8, 26))
    def test_edition_after_begin_but_before_qualif(self):
        self.assertPhaseIs(None, 'future')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2015, 9, 1) - timedelta(seconds=1))
    def test_qualif_just_before_begin(self):
        self.assertPhaseIs(None, 'future')

    @mock_dt(datetime(2015, 9, 1) + timedelta(seconds=1))
    def test_qualif_just_after_begin(self):
        self.assertPhaseIs(Event.Type.qualification, 'active')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 1, 1) - timedelta(seconds=1))
    def test_qualif_just_before_end(self):
        self.assertPhaseIs(Event.Type.qualification, 'active')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 1, 1) + timedelta(seconds=1))
    def test_qualif_just_after_end(self):
        self.assertPhaseIs(Event.Type.qualification, 'done')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 1, 2))
    def test_qualif_corrected(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.qualification, 'corrected')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 2, 1) - timedelta(seconds=1))
    def test_semi_just_before_begin(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.qualification, 'corrected')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 2, 1) + timedelta(seconds=1))
    def test_semi_just_after_begin(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'active')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 2, 20))
    def test_semi_active(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'active')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 4, 1))
    def test_semi_still_active(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'active')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 4, 2) - timedelta(seconds=1))
    def test_semi_just_before_end(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'active')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 4, 2) + timedelta(seconds=1))
    def test_semi_just_after_end(self):
        self.edition.qualification_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'done')
        self.assertCanEdit(self.noob_user)
        self.assertCanNotEdit(self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 4, 2) + timedelta(seconds=1))
    def test_semi_corrected(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'corrected')
        self.assertCanEdit(self.noob_user, self.semifinal_user)
        self.assertCanNotEdit(self.final_user)

    @mock_dt(datetime(2016, 5, 20) - timedelta(seconds=1))
    def test_final_just_before_begin(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.assertPhaseIs(Event.Type.semifinal, 'corrected')
        self.assertCanEdit(self.noob_user, self.semifinal_user)
        self.assertCanNotEdit(self.final_user)

    @mock_dt(datetime(2016, 5, 20) + timedelta(seconds=1))
    def test_final_just_after_begin(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.assertPhaseIs(Event.Type.final, 'active')
        self.assertCanEdit(self.noob_user, self.semifinal_user)
        self.assertCanNotEdit(self.final_user)

    @mock_dt(datetime(2016, 5, 23) - timedelta(seconds=1))
    def test_final_just_before_end(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.assertPhaseIs(Event.Type.final, 'active')
        self.assertCanEdit(self.noob_user, self.semifinal_user)
        self.assertCanNotEdit(self.final_user)

    @mock_dt(datetime(2016, 5, 23) + timedelta(seconds=1))
    def test_final_just_after_end(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.assertPhaseIs(Event.Type.final, 'done')
        self.assertCanEdit(self.noob_user, self.semifinal_user)
        self.assertCanNotEdit(self.final_user)

    @mock_dt(datetime(2016, 5, 23) + timedelta(seconds=1))
    def test_final_corrected(self):
        self.edition.qualification_corrected = True
        self.edition.semifinal_corrected = True
        self.edition.final_corrected = True
        self.assertPhaseIs(None, 'finished')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)

    @mock_dt(datetime(2016, 7, 1))
    def test_edition_after_end(self):
        self.assertPhaseIs(None, 'finished')
        self.assertCanEdit(self.noob_user, self.semifinal_user, self.final_user)
