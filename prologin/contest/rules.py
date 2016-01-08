import rules


@rules.predicate
def event_is_active(user, event):
    return event.is_active


rules.add_perm('contest.submit_qualification', rules.is_authenticated & event_is_active)
rules.add_perm('correction.can_correct', rules.is_staff)
