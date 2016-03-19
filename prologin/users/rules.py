import rules
from django.core.exceptions import SuspiciousOperation


@rules.predicate
def can_impersonate(hijacker, hijacked):
    # Nobody can impersonate superusers
    if hijacked.is_superuser:
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


rules.add_rule('can_impersonate_user', can_impersonate)
rules.add_perm('users.may_impersonate', rules.is_staff)


def hijack_authorization_check(hijacker, hijacked):
    """
    Custom check for django-hijack
    """
    return rules.test_rule('can_impersonate_user', hijacker, hijacked)


def hijack_forbidden(*args, **kwargs):
    """
    Prevent calling django-hijack CSRF-exposed views
    """
    def view(*args, **kwargs):
        raise SuspiciousOperation("Trying to access monkey-patched function")
    return view
