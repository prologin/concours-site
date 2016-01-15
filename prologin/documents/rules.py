import rules


@rules.predicate
def is_contestant_owner(contestant, user):
    return contestant.user == user


rules.add_perm('documents.generate_batch_document', rules.is_staff)
rules.add_perm('documents.generate_contestant_document', rules.is_staff | is_contestant_owner)
rules.add_perm('documents.view_tex_errors', rules.is_staff)
