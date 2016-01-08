import rules


@rules.predicate
def can_view_qcm(user, qcm):
    return not qcm.event.is_in_future


@rules.predicate
def can_save_answers(user, qcm):
    return qcm.event.is_active


@rules.predicate
def can_view_correction(user, qcm):
    return qcm.event.is_finished


rules.add_perm('qcm.view_qcm', rules.is_staff | can_view_qcm)
rules.add_perm('qcm.view_correction', can_view_qcm & can_view_correction)
rules.add_perm('qcm.save_answers', can_view_qcm & rules.is_authenticated & can_save_answers)
