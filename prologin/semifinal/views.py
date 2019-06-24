# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib.auth import get_user_model
from django.db.models.aggregates import Sum
from django.http import JsonResponse
from django.template.loader import get_template
from django.views.generic import TemplateView, View
from rules.contrib.views import PermissionRequiredMixin

from problems.models import Submission
from prologin.utils.scoring import decorate_with_rank

User = get_user_model()


class ScoreboardUserListMixin:
    def get_user_list(self):
        users = (User.objects
                 .filter(is_active=True, is_staff=False, is_superuser=False)
                 .annotate(score=Sum(Submission.get_score_func('training_submissions')))
                 .order_by('-score', 'username'))

        def score_getter(user):
            return user.score

        def decorator(user, rank, ex_aequo):
            user.rank = rank
            user.ex_aequo = ex_aequo

        decorate_with_rank(users, score_getter, decorator)
        return users


class ParticipateRequiredMixin(PermissionRequiredMixin):
    permission_required = 'semifinal.participate'


class Homepage(ParticipateRequiredMixin, TemplateView):
    template_name = 'semifinal/homepage.html'


class Scoreboard(ScoreboardUserListMixin, TemplateView):
    template_name = 'semifinal/scoreboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = self.get_user_list()
        return context


class ScoreboardData(ScoreboardUserListMixin, View):
    def get(self, context, **kwargs):
        return JsonResponse(self.get_json_data(), safe=False)

    def get_json_data(self):
        users = self.get_user_list()
        template = get_template('semifinal/stub-scoreboard-item.html')
        return [{'id': '#sb-{}'.format(user.pk), 'html': template.render({'user': user})}
                for user in users]
