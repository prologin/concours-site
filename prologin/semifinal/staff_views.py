from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.db.models.aggregates import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from rules.contrib.views import PermissionRequiredMixin

import contest.models
import problems
from problems.models import Submission
import semifinal.forms


class MonitorPermissionMixin(PermissionRequiredMixin):
    permission_required = 'semifinal.monitor'


class MonitoringIndexView(MonitorPermissionMixin, TemplateView):
    template_name = 'semifinal/monitoring.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contestants = (contest.models.Contestant.objects
                       .select_related('user')
                       .filter(user__is_staff=False, user__is_superuser=False,
                               edition=self.request.current_edition)
                       .annotate(score=Sum(
                           Submission.get_score_func('user__training_submissions')))
                       .order_by('user__username'))
        now = timezone.now()
        for contestant in contestants:
            # extend available_semifinal_problems with more attributes and store it as semifinal_problems
            max_difficulty = 0
            problems = contestant.available_semifinal_problems
            for problem, dates in problems.items():
                delta = None
                concerning = ''
                if dates['solved']:
                    delta = dates['solved'] - dates['unlocked']
                    max_difficulty = max(max_difficulty, problem.difficulty)
                else:
                    warning, danger = settings.SEMIFINAL_CONCERNING_TIME_SPENT
                    seconds = (now - dates['unlocked']).seconds
                    if seconds > danger:
                        concerning = 'danger'
                    elif seconds > warning:
                        concerning = 'warning'
                dates['delta'] = delta
                dates['concerning'] = concerning
            contestant.max_difficulty = max_difficulty
            contestant.semifinal_problems = sorted(problems.items(), key=lambda p: p[1]['unlocked'], reverse=True)
        context['contestants'] = contestants
        return context


class ExplicitUnlockView(FormView):
    template_name = 'semifinal/explicit-unlock.html'
    form_class = semifinal.forms.ExplicitProblemUnlockForm
    success_url = reverse_lazy('monitoring:index')

    def form_valid(self, form):
        problem_name = form.cleaned_data['problem']
        # We cannot bulk create, because it will fail it unlock already exists
        created = 0
        existing = 0
        for contestant in form.cleaned_data['contestants']:
            unlock = problems.models.ExplicitProblemUnlock(challenge=self.request.current_challenge,
                                                           problem=problem_name,
                                                           user=contestant.user,
                                                           created_by=self.request.user)
            try:
                unlock.save()
                created += 1
            except IntegrityError:
                existing += 1

        problem = self.request.current_challenge.problem(problem_name)
        messages.success(self.request,
                         format_html(_("Unlocked <em>{problem}</em> for {created} users; {existing} unlocks were already set."),
                                     problem=problem.title, created=created, existing=existing))
        return super().form_valid(form)

    def get_form_kwargs(self):
        contestant = self.request.GET.get('contestant')
        allfirst = self.request.GET.get('allfirst')
        kwargs = super().get_form_kwargs()
        kwargs['challenge'] = self.request.current_challenge
        if contestant:
            contestant = get_object_or_404(contest.models.Contestant, pk=contestant)
            kwargs['initial'] = {'contestants': [contestant]}
        elif allfirst:
            contestants = contest.models.Contestant.objects.filter(user__is_staff=False, user__is_superuser=False)
            problem = self.request.current_challenge.problems[0].name
            kwargs['initial'] = {'contestants': contestants, 'problem': problem}
        return kwargs
