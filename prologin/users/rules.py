import rules
from django.core.exceptions import SuspiciousOperation


@rules.predicate
def can_impersonate(hijacker, hijacked):
    # Inactive users cannot be hijacked
    if not hijacked.is_active:
        return False
    # Superusers can impersonate staff & members
    if hijacker.is_superuser:
        return True
    # Inactive users cannot be hijacked
    return hijacked.is_active and hijacker.is_superuser


@rules.predicate
def is_self(user, edited_user):
    return user == edited_user


# A *rule* so we can use check_rule, because check_perm always returns True for
# superusers, defeating the checks in can_impersonate
rules.add_rule('users.can-impersonate', can_impersonate)
rules.add_perm('users.search', rules.is_staff)
rules.add_perm('users.edit', rules.is_superuser | is_self)
rules.add_perm('users.edit-during-contest', rules.is_staff)
rules.add_perm('users.delete', rules.is_superuser | is_self)
rules.add_perm('users.takeout', rules.is_superuser | is_self)
rules.add_perm('users.external-auth', rules.is_authenticated)


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
