from collections import namedtuple, defaultdict
from django import forms
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import contest.models
import problems.models

User = get_user_model()
SemifinalResults = namedtuple('SemifinalResults', 'event contestants submissions submissioncodes explicitunlocks')


class ImportSemifinalResultUploadForm(forms.Form):
    file = forms.FileField(label=_("JSON export file"),
                           required=True,
                           help_text=_("Select the JSON export file obtained from regional event website and proceed."))

    def clean_file(self):
        stream = self.cleaned_data['file']
        stream.seek(0)
        deserializer = serializers.get_deserializer('json')

        invalid_format = _("Invalid format: could not read or deserialize %(type)s")

        try:
            import_edition = next(deserializer(stream.readline())).object
        except Exception:
            raise ValidationError(invalid_format % {'type': "Edition"})
        try:
            edition = contest.models.Edition.objects.get(pk=import_edition.pk)
        except contest.models.Edition.DoesNotExist:
            raise ValidationError(_("Imported edition is invalid."))

        try:
            import_center = next(deserializer(stream.readline())).object
        except Exception:
            raise ValidationError(invalid_format % {'type': "Center"})
        try:
            center = contest.models.Center.objects.get(pk=import_center.pk)
        except contest.models.Center.DoesNotExist:
            raise ValidationError(_("Imported center is invalid."))

        try:
            import_event = next(deserializer(stream.readline())).object
        except Exception:
            raise ValidationError(invalid_format % {'type': "Event"})
        try:
            event = contest.models.Event.objects.get(pk=import_event.pk)
        except contest.models.Event.DoesNotExist:
            raise ValidationError(_("Imported event is invalid."))

        if event.edition != edition or event.center != center:
            raise ValidationError(_("Imported event edition or center mismatches with known event."))

        try:
            import_users = deserializer(stream.readline())
        except Exception:
            raise ValidationError(invalid_format % {'type': "User"})
        user_pks = [user.object.pk for user in import_users]
        if User.objects.filter(pk__in=user_pks).count() != len(user_pks):
            raise ValidationError(_("Imported users mismatch."))

        try:
            import_contestants = [item.object for item in deserializer(stream.readline())]
        except Exception:
            raise ValidationError(invalid_format % {'type': "Contestant"})

        contestant_pks = set(contestant.pk for contestant in import_contestants)
        challenge = event.challenge
        our_contestants = {contestant.pk: contestant
                           for contestant in (contest.models.Contestant.objects
                                              .filter(pk__in=contestant_pks)
                                              .select_related('edition', 'user', 'assignation_semifinal_event'))}
        contestants = [(contestant, our_contestants.get(contestant.pk)) for contestant in import_contestants]

        try:
            import_submissions = list(deserializer(stream.readline()))
            import_codes = list(deserializer(stream.readline()))
            import_explicitunlocks = list(deserializer(stream.readline()))
        except Exception:
            raise ValidationError(invalid_format % {'type': "Submission/SubmissionCode/ExplicitProblemUnlock"})

        user_submissions = defaultdict(list)
        for item in import_submissions:
            user_submissions[item.object.user_id].append(item.object)
        submission_codes = defaultdict(list)
        for item in import_codes:
            submission_codes[item.object.submission_id].append(item.object)
        problem_unlocks = defaultdict(list)
        for item in import_explicitunlocks:
            problem_unlocks[(item.object.user_id, item.object.problem)].append(item.object)

        for contestant, our in contestants:
            contestant.submissions = sorted(user_submissions[contestant.user_id],
                                            key=lambda s: challenge.problem(s.problem).difficulty)
            contestant.score = sum(sub.score() for sub in contestant.submissions)
            for submission in contestant.submissions:
                submission.all_codes = submission_codes[submission.id]
                submission.code_count = len(submission.all_codes)
                submission.unlock = problem_unlocks[(contestant.user_id, submission.problem)]

        contestants.sort(key=lambda pair: pair[0].score, reverse=True)
        return SemifinalResults(event, contestants, import_submissions, import_codes, import_explicitunlocks)


class ImportSemifinalResultReviewForm(forms.Form):
    pass


DAY_OF_WEEK = (
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
    ('7', 'Sunday'),
)

TIME_OF_DAY = (
    ('1', 'Morning'),
    ('2', 'Noon'),
    ('3', 'Evening'),
)

class MealTicketForm(forms.Form):
    ticket_day = forms.ChoiceField(choices=DAY_OF_WEEK, label='Ticket name')
    ticket_day_nb = forms.ChoiceField(choices=list(zip(range(1, 32), range(1,32))), label='')
    ticket_day_time = forms.ChoiceField(choices=TIME_OF_DAY, label='')
    ticket_id = forms.IntegerField(label='Starting ID', min_value=0, max_value=999, initial=1)

    def __init__(self, *args, **kwargs):
        super(MealTicketForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'input-sm'})


class BadgesOrganizersForm(forms.Form):
    name = forms.CharField(label='Name :', widget=forms.Textarea)
