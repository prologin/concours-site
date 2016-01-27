import rules
import contest.models


@rules.predicate
def can_download_semifinal(user, contestant):
    return (contestant.user == user and
            contestant.edition.qualification_corrected and
            contestant.assignation_semifinal == contest.models.Assignation.assigned.value)


@rules.predicate
def can_download_final(user, contestant):
    return (contestant.user == user and
            contestant.edition.semifinal_corrected and
            contestant.assignation_final == contest.models.Assignation.assigned.value)


rules.add_perm('documents.generate_batch_document', rules.is_staff)
rules.add_perm('documents.generate_data_export', rules.is_staff)
rules.add_perm('documents.generate_semifinal_contestant_document', rules.is_staff | can_download_semifinal)
rules.add_perm('documents.generate_final_contestant_document', rules.is_staff | can_download_final)
rules.add_perm('documents.view_tex_errors', rules.is_staff)
