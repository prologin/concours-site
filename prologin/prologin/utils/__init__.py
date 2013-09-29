from django.template import VariableDoesNotExist, Variable
from django.core.urlresolvers import reverse
from django.utils.html import escape
import unicodedata
import string
import re

def get_slug(name):
    name = unicodedata.normalize('NFKD', name.lower())
    name = ''.join(x for x in name if x in string.ascii_letters + string.digits + ' _-')
    name = re.sub(r'[^a-z0-9\-]', '_', name)
    return name

def custom_expand(var, context):
    from users.models import UserProfile
    from team.models import Team

    if not isinstance(var, str):
        return var

    if var.find('{{me}}') != -1 and context['request'].user.is_authenticated():
        profile = UserProfile.objects.get(user__id=context['request'].user.id)
        var = var.replace('{{me}}', profile.slug)

    if var.find('{{last_edition}}') != -1:
        # Issue #6
        last = Team.objects.values('year').distinct().order_by('-year')[:1][0]
        var = var.replace('{{last_edition}}', str(last['year']))

    return var

def real_value(var, context):
    """Return the real value based on the context."""
    if var is None:
        return None
    try:
        if not isinstance(var, Variable):
            var = Variable(var)
        real_var = var.resolve(context)
    except (VariableDoesNotExist):
        real_var = str(var)

    real_var = custom_expand(real_var, context)
    return escape(real_var)

def get_url(params):
    ret = None
    if len(params) > 1:
        ret = reverse(params[0], args=params[1:])
    else:
        ret = reverse(params[0]) if params[0] != 'none' else None
    return ret

def get_real_url(url, context):
    ret = url
    if url[0] not in ['/', '#'] and url.find('://') == -1:
        args = url.split('|')
        args = [custom_expand(_, context) for _ in args]
        url = args.pop(0)
        ret = reverse(url, args=args)
    return ret
