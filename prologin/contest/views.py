from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import ListView
from rules.contrib.views import PermissionRequiredMixin

import contest.forms
import contest.models
import problems.models
import schools.models


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
            issues.append(_("You cannot participate if you are born before {}.").format(birth_year))

        return context


class SchoolSearch(LoginRequiredMixin, ListView):
    model = schools.models.School
    paginate_by = 5
    max_facebook_results = 3

    @cached_property
    def query(self):
        return self.request.GET.get('q', '')

    def get_queryset(self):
        qs = Q(name__icontains=self.query, approved=True)
        current_school = self.request.current_contestant.school
        if current_school:
            qs |= Q(name__icontains=self.query, pk=current_school.pk)
        return super().get_queryset().filter(qs)

    def render_to_response(self, context, **response_kwargs):
        paginator = context['paginator']
        # Database results
        results = [{'id': school.pk,
                    'text': school.name,
                    'picture': school.picture}
                   for school in context['object_list']]
        known_names = {item['text'].lower() for item in results}
        # Facebook results
        fb_results = []
        for result in schools.models.Facebook.search(self.query):
            if result['name'].lower() in known_names:
                continue
            fb_results.append({'id': '_new_fb_{}'.format(result['id']),
                               'text': result['name'],
                               'picture': result['picture']['data']['url']})
            if len(fb_results) == self.max_facebook_results:
                break
        results += fb_results
        return JsonResponse({
            'items': results,
            'total': paginator.count + len(fb_results),
        })
