from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.template.loader import get_template
from django.views.generic import TemplateView, View
from rules.contrib.views import PermissionRequiredMixin

from prologin.utils.scoring import decorate_with_rank

User = get_user_model()


class ScoreboardUserListMixin:
    def get_user_list(self):
        users = (User.objects
                 .filter(is_active=True, is_staff=False, is_superuser=False)
                 .annotate(score=Coalesce(Sum('training_submissions__score_base') - Sum('training_submissions__malus'), 0))
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


class Scoreboard(ScoreboardUserListMixin, ParticipateRequiredMixin, TemplateView):
    template_name = 'semifinal/scoreboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = self.get_user_list()
        return context


class ScoreboardData(ScoreboardUserListMixin, ParticipateRequiredMixin, View):
    def get(self, context, **kwargs):
        return JsonResponse(self.get_json_data(), safe=False)

    def get_json_data(self):
        users = self.get_user_list()
        template = get_template('semifinal/stub-scoreboard-item.html')
        return [{'id': '#sb-{}'.format(user.pk), 'html': template.render({'user': user})}
                for user in users]
