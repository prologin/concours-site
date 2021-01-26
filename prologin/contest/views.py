from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView, FormView
from django.views.generic.edit import ModelFormMixin
from rules.contrib.views import PermissionRequiredMixin

import contest.forms
import contest.models
import problems.models

from contest import event_wishes_override


# TODO:
# - decide if year URL arg is just decoration (we have current edition in settings) or if it has a meaning
# - refactor summary code with jumbotron


class QualificationSummary(PermissionRequiredMixin, UpdateView):
    template_name = 'contest/qualification-summary.html'
    pk_url_kwarg = 'year'
    context_object_name = 'contestant'
    form_class = contest.forms.CombinedContestantUserForm
    model = contest.models.Contestant
    permission_required = 'contest.submit_qualification'

    def get_permission_object(self):
        return self.request.current_events['qualification']

    def get_object(self, queryset=None):
        # available from prologin.middleware.ContestMiddleware
        return self.request.current_contestant

    def get_success_url(self):
        return reverse('contest:qualification-summary', kwargs=self.kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if kwargs.get('instance') is not None:
            kwargs['instance'] = {
                'contestant': kwargs['instance'],
                'user': kwargs['instance'].user,
            }
        kwargs['edition'] = self.request.current_edition
        kwargs['complete'] = self.request.current_contestant.is_complete_for_semifinal
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            objects = form.save(commit=False)
            self.object = objects['contestant']
            self.object.save()
            self.object.assignation_semifinal_wishes.clear()
            for i, event in enumerate(event for event in form.cleaned_data['contestant']['assignation_semifinal_wishes'] if event):
                contest.models.EventWish(contestant=self.object, event=event, order=i).save()
            user = objects['user']
            user.save()
        messages.success(self.request, _("Changes saved successfully."))
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contestant = self.object

        if self.request.current_qcm:
            context['quiz_question_count'] = self.request.current_qcm.question_count
            context['completed_quiz_question_count'] = self.request.current_qcm.completed_question_count_for(contestant)

        current_qualif_challenge = self.request.current_events['qualification'].challenge
        qualif_problem_answers = problems.models.Submission.objects.filter(user=self.request.user,
                                                                           challenge=current_qualif_challenge.name)

        context['problem_count'] = len(current_qualif_challenge.problems)
        context['completed_problem_count'] = qualif_problem_answers.count()

        context['issues'] = issues = []

        if not contestant.has_mandatory_info:
            issues.append(_("You are missing some mandatory information."))
        if not contestant.has_enough_semifinal_wishes:
            issues.append(_("You need to specify more wishes for your semifinal center."))
        if not contestant.is_young_enough:
            birth_year = settings.PROLOGIN_EDITION - settings.PROLOGIN_MAX_AGE
            issues.append(_("You cannot participate if you are born before %(year)s.") % {'year': birth_year})

        return context

class ContestantSemifinalEventSelection(event_wishes_override.CanOverrideEventWishMixin,FormView):
    form_class = contest.forms.ContestantSemifinalEventForm
    template_name = 'contest/semifinal-center-choice.html'
    success_url = reverse_lazy('home')

    def get_form(self, form_class=None):
        self.possible_events = contest.models.Event.semifinals_for_edition(self.request.current_data.edition.year)
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(possible_events=tuple((e.id, str(e)) for e in self.possible_events), **self.get_form_kwargs())

    def form_valid(self, form):
        with transaction.atomic():
            contestant = self.request.current_data.current_contestant
            event = self.possible_events.get(id=form.cleaned_data['selected_event'])
            contest.models.EventWish.objects.filter(contestant=contestant).delete()
            wish = contest.models.EventWish(event=event, contestant=contestant, order=1)
            wish.save()
            contestant.assignation_semifinal_wishes.set([wish.event])
            contestant.save()

        return super().form_valid(form)
