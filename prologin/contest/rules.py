import rules


# Permissions
rules.add_perm('correction.can_correct', rules.is_staff)
