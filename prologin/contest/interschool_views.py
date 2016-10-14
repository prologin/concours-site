from django.views.generic import ListView
from rules.contrib.views import PermissionRequiredMixin

import schools.models
import problems.models

import contest.models
from prologin.utils.scoring import Scoreboard


class SchoolScoreboard(Scoreboard):
    def get_score(self, item):
        return item.final_score


class LeaderboardView(PermissionRequiredMixin, ListView):
    template_name = 'contest/interschool-leaderboard.html'
    model = schools.models.School
    context_object_name = 'schools'
    permission_required = 'contest.interschool.view_leaderboard'
    # paginate_by = 42

    def get_permission_object(self):
        return self.request.current_edition

    def get_queryset(self):
        edition = self.request.current_edition
        challenge = problems.models.Challenge.by_year_and_event_type(
            edition.year, contest.models.Event.Type.qualification)
        return super().get_queryset().raw('''
            SELECT
                schools_school.*,
                COUNT(DISTINCT contest_contestant.id) AS contestant_count,
                SUM(CASE WHEN problems_submission.score_base > 0 THEN 1 ELSE 0 END) AS problem_solved_count,
                SUM(CASE WHEN problems_submission.score_base > 0
                    THEN problems_submission.score_base - problems_submission.malus
                    ELSE 0 END) AS final_score
            FROM schools_school
                LEFT JOIN contest_contestant ON schools_school.id = contest_contestant.school_id AND contest_contestant.edition_id = %s
                LEFT JOIN users_prologinuser ON contest_contestant.user_id = users_prologinuser.id
                LEFT JOIN problems_submission ON problems_submission.user_id = users_prologinuser.id AND problems_submission.challenge = %s
            WHERE schools_school.approved
            GROUP BY schools_school.id
            ORDER BY final_score DESC, problem_solved_count DESC, schools_school.name ASC
            LIMIT 42
        ''', (edition.pk, challenge.name))
        # case = models.Case(models.When(contestants__edition=edition, then=1), default=0,
        #                    output_field=models.IntegerField())
        # return (super().get_queryset()
        #         .annotate(contestant_count=models.Sum(case))
        #         .order_by('-contestant_count', 'name'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = SchoolScoreboard(context[self.context_object_name])
        return context
