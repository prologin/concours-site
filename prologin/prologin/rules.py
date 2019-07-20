import rules

# Allow staff to view and edit templates/queries, but not send batches
rules.add_perm('massmailer.change_template', rules.is_staff)
rules.add_perm('massmailer.view_template', rules.is_staff)
rules.add_perm('massmailer.create_template', rules.is_staff)
rules.add_perm('massmailer.delete_template', rules.is_staff)
rules.add_perm('massmailer.change_query', rules.is_staff)
rules.add_perm('massmailer.view_query', rules.is_staff)
rules.add_perm('massmailer.create_query', rules.is_staff)
rules.add_perm('massmailer.delete_query', rules.is_staff)
rules.add_perm('massmailer.view_batch', rules.is_staff)
