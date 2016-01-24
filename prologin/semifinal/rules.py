import rules


rules.add_perm('semifinal.monitor', rules.is_staff)
rules.add_perm('semifinal.participate', rules.is_authenticated & rules.is_active)
