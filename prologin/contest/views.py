from django.conf import settings
from django.db import transaction
from django.views.generic import UpdateView
from django.views.generic.edit import ModelFormMixin
from django.core.urlresolvers import reverse

from prologin.utils import LoginRequiredMixin
import contest.forms
import contest.models
import problems.models

# TODO:
# - decide if year URL arg is just decoration (we have current edition in settings) or if it has a meaning
# - refactor summary code with jumbotron


class QualificationSummary(LoginRequiredMixin, UpdateView):
    template_name = 'contest/qualification_summary.html'
    pk_url_kwarg = 'year'
    context_object_name = 'contestant'
    form_class = contest.forms.CombinedContestantUserForm
    model = contest.models.Contestant

    def get_object(self, queryset=None):
        # available from prologin.middleware.ContestMiddleware
        return self.request.current_contestant

    def get_success_url(self):
        return reverse('contest:qualification_summary', kwargs=self.kwargs)

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
            self.object.event_wishes.clear()
            for i, event in enumerate(event for event in form.cleaned_data['contestant']['event_wishes'] if event):
                contest.models.EventWish(contestant=self.object, event=event, order=i).save()
            user = objects['user']
            user.save()
        return super(ModelFormMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contestant = self.object

        if self.request.current_qcm:
            context['quiz_question_count'] = self.request.current_qcm.question_count
            context['completed_quiz_question_count'] = self.request.current_qcm.completed_question_count_for(contestant)
            context['quiz_completed'] = self.request.current_qcm.is_completed_for(self.request.current_contestant)

        current_qualif_challenge = self.request.current_events['qualification'].challenge
        qualif_problem_answers = problems.models.Submission.objects.filter(user=self.request.user,
                                                                           challenge=current_qualif_challenge.name)

        problem_count = len(current_qualif_challenge.problems)
        completed_problem_count = qualif_problem_answers.count()
        context['problem_count'] = problem_count
        context['completed_problem_count'] = completed_problem_count
        context['problems_completed'] = problem_count == completed_problem_count

        return context
