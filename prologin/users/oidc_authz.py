from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from .models import OpenIDClientPolicy

def authorize(request, user, client):
    policy = None
    try:
        policy = OpenIDClientPolicy.objects.get(openid_client=client)
    except ObjectDoesNotExist:
        # No policy <=> not altering anything
        return

    if not policy.is_user_allowed(user):
        raise PermissionDenied
