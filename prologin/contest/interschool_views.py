from django.conf import settings
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
    paginate_by = 42

    def get_permission_object(self):
        return self.request.current_edition

    def get_queryset(self):
        edition = self.request.current_edition
        challenge = problems.models.Challenge.by_year_and_event_type(
            edition.year, contest.models.Event.Type.qualification)
        min_birth_year = edition.year - settings.PROLOGIN_MAX_AGE
        qs = super().get_queryset().raw('''
            WITH ContestantScores AS (
                SELECT
                    contest_contestant.school_id,
                    contest_contestant.id AS contestant_id,
                    SUM(problems_submission.score_base - problems_submission.malus) AS total_score,
                    COUNT(CASE WHEN problems_submission.score_base > 0 THEN 1 ELSE NULL END) AS problems_solved
                FROM contest_contestant
                INNER JOIN users_prologinuser ON contest_contestant.user_id = users_prologinuser.id
                    AND users_prologinuser.birthday IS NOT NULL
                    AND EXTRACT(YEAR FROM users_prologinuser.birthday) >= %s
                LEFT JOIN problems_submission ON problems_submission.user_id = users_prologinuser.id
                    AND problems_submission.challenge = %s
                WHERE contest_contestant.edition_id = %s
                GROUP BY contest_contestant.school_id, contest_contestant.id
                HAVING SUM(problems_submission.score_base - problems_submission.malus) > 0
            ),
            RankedScores AS (
                SELECT
                    school_id,
                    total_score,
                    problems_solved,
                    ROW_NUMBER() OVER (
                        PARTITION BY school_id
                        ORDER BY total_score DESC
                    ) AS rank
                FROM ContestantScores
            )
            SELECT
                schools_school.*,
                (SELECT COUNT(*) FROM ContestantScores WHERE ContestantScores.school_id = schools_school.id) AS contestant_count,
                (SELECT SUM(problems_solved) FROM ContestantScores WHERE ContestantScores.school_id = schools_school.id) AS problem_solved_count,
                ROUND(SUM(CAST(total_score AS FLOAT) * POWER(0.8, rank - 1) * 100/35)) AS final_score
            FROM schools_school
            LEFT JOIN RankedScores ON schools_school.id = RankedScores.school_id
            WHERE schools_school.approved
            GROUP BY schools_school.id
            HAVING SUM(total_score) > 0
            ORDER BY final_score DESC, problem_solved_count DESC, schools_school.name ASC
        ''', (min_birth_year, challenge.name, edition.pk))
        return SchoolScoreboard(qs)
