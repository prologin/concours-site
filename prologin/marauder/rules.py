import rules
import team.models


@rules.predicate
def is_team_member(user, _):
    return team.models.TeamMember.objects.filter(user=user).exists()

# Permissions
rules.add_perm('marauder.get-geofences', rules.always_allow)
rules.add_perm('marauder.get-settings', rules.always_allow)
rules.add_perm('marauder.report', rules.is_authenticated &
               (rules.is_staff | is_team_member))
rules.add_perm('marauder.view', rules.is_authenticated &
               (rules.is_staff | is_team_member))
