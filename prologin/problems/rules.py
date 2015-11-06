import rules


@rules.predicate
def is_challenge_displayable(user, challenge):
    return challenge.displayable


@rules.predicate
def can_view_problem(user, problem):
    return is_challenge_displayable(user, problem.challenge)


@rules.predicate
def is_code_submission_owner(user, code):
    return user == code.submission.user


# Permissions
rules.add_perm('problems.view_challenge', rules.is_staff | is_challenge_displayable)
rules.add_perm('problems.view_problem', rules.is_staff | can_view_problem)
rules.add_perm('problems.view_code_submission', rules.is_staff | is_code_submission_owner)
rules.add_perm('problems.create_problem_code_submission', rules.is_staff | can_view_problem)
