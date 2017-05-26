import rules
from django.core.exceptions import SuspiciousOperation


@rules.predicate
def can_impersonate(hijacker, hijacked):
    # Nobody can impersonate superusers
    if hijacked.is_superuser:
        return False
    # Inactive users cannot be hijacked
    if not hijacked.is_active:
        return False
    # Superusers can impersonate staff & members
    if hijacker.is_superuser:
        return True
    # Have to be staff
    if not hijacker.is_staff:
        return False
    # Staff can not impersonate staff
    if hijacked.is_staff:
        return False
    return True


@rules.predicate
def is_self(user, edited_user):
    return user == edited_user


# A *rule* so we can use check_rule, because check_perm always returns True for superusers,
# defeating the checks in can_impersonate
rules.add_rule('users.can-impersonate', can_impersonate)
rules.add_perm('users.may-impersonate', rules.is_staff)
rules.add_perm('users.search', rules.is_staff)
rules.add_perm('users.edit', rules.is_staff | is_self)
rules.add_perm('users.edit-during-contest', rules.is_staff)


def hijack_authorization_check(hijacker, hijacked):
    """
    Custom check for django-hijack
    """
    return rules.test_rule('users.can-impersonate', hijacker, hijacked)


def hijack_forbidden(*args, **kwargs):
    """
    Prevent calling django-hijack CSRF-exposed views
    """
    def view(*args, **kwargs):
        raise SuspiciousOperation("Trying to access monkey-patched function")
    return view
