import rules


@rules.predicate
def event_is_active(user, event):
    return event and event.is_active


@rules.predicate
def edition_is_active(user, edition):
    return edition and edition.is_active


@rules.predicate
def can_download_home(user, contestant):
    return contestant.is_home_public or contestant.user == user


rules.add_perm('contest.submit_qualification', rules.is_authenticated & event_is_active)
rules.add_perm('correction.can_correct', rules.is_staff)
rules.add_perm('contest.can_download_home', can_download_home | rules.is_staff)

rules.add_perm('contest.interschool.view_leaderboard', edition_is_active)
