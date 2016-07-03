import unittest.mock
from datetime import datetime, timedelta

from django.utils.timezone import make_aware

from contest.models import Edition, Event
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
                                              date_begin=make_aware(datetime(2015, 9, 1)),
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

    def tearDown(self):
        Edition.objects.all().delete()

    def assertPhaseAre(self, qualif, semi, final):
        phase = self.edition.phase
        self.assertEqual(phase[Event.Type.qualification.name], qualif)
        self.assertEqual(phase[Event.Type.semifinal.name], semi)
        self.assertEqual(phase[Event.Type.final.name], final)

    @mock_dt(datetime(2015, 8, 1))
    def test_edition_future(self):
        self.assertPhaseAre(qualif='future', semi='future', final='future')

    @mock_dt(datetime(2015, 9, 1) - timedelta(seconds=1))
    def test_qualif_just_before(self):
        self.assertPhaseAre(qualif='future', semi='future', final='future')

    @mock_dt(datetime(2015, 9, 1))
    def test_qualif_active(self):
        self.assertPhaseAre(qualif='active', semi='future', final='future')

    @mock_dt(datetime(2015, 12, 30))
    def test_qualif_active_2(self):
        self.assertPhaseAre(qualif='active', semi='future', final='future')

    @mock_dt(datetime(2016, 1, 2))
    def test_qualif_done(self):
        self.assertPhaseAre(qualif='done', semi='future', final='future')

    @mock_dt(datetime(2016, 1, 2))
    def test_qualif_done_corrected(self):
        self.edition.qualification_corrected = True
        self.assertPhaseAre(qualif='corrected', semi='future', final='future')

    @mock_dt(datetime(2016, 2, 1) - timedelta(seconds=1))
    def test_semi_just_before(self):
        self.assertPhaseAre(qualif='done', semi='future', final='future')

    @mock_dt(datetime(2016, 2, 1))
    def test_semi_active(self):
        self.assertPhaseAre(qualif='done', semi='active', final='future')

    @mock_dt(datetime(2016, 2, 20))
    def test_semi_active_2(self):
        self.assertPhaseAre(qualif='done', semi='active', final='future')

    @mock_dt(datetime(2016, 4, 1))
    def test_semi_active_3(self):
        self.assertPhaseAre(qualif='done', semi='active', final='future')

    @mock_dt(datetime(2016, 4, 2) - timedelta(seconds=1))
    def test_semi_done_just_before(self):
        self.assertPhaseAre(qualif='done', semi='active', final='future')

    @mock_dt(datetime(2016, 4, 2) + timedelta(seconds=1))
    def test_semi_done(self):
        self.assertPhaseAre(qualif='done', semi='done', final='future')

    @mock_dt(datetime(2016, 4, 2) + timedelta(seconds=1))
    def test_semi_done_corrected(self):
        self.edition.semifinal_corrected = True
        self.assertPhaseAre(qualif='done', semi='corrected', final='future')

    @mock_dt(datetime(2016, 5, 20) - timedelta(seconds=1))
    def test_final_just_before(self):
        self.assertPhaseAre(qualif='done', semi='done', final='future')

    @mock_dt(datetime(2016, 5, 20) + timedelta(seconds=1))
    def test_final_just_after(self):
        self.assertPhaseAre(qualif='done', semi='done', final='active')

    @mock_dt(datetime(2016, 5, 23) - timedelta(seconds=1))
    def test_final_done_just_before(self):
        self.assertPhaseAre(qualif='done', semi='done', final='active')

    @mock_dt(datetime(2016, 5, 23) + timedelta(seconds=1))
    def test_final_done_just_after(self):
        self.assertPhaseAre(qualif='done', semi='done', final='done')

    @mock_dt(datetime(2016, 5, 23) + timedelta(seconds=1))
    def test_final_done_corrected(self):
        self.edition.final_corrected = True
        self.assertPhaseAre(qualif='done', semi='done', final='corrected')

    @mock_dt(datetime(2016, 6, 1))
    def test_edition_finished(self):
        self.assertPhaseAre(qualif='finished', semi='finished', final='finished')
