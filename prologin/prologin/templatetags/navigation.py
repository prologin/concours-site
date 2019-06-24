from django import template
from django.http import QueryDict
from django.urls import reverse, NoReverseMatch
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.search(pattern, path):
        return 'active'
    return ''


@register.simple_tag
def querystring(request=None, **kwargs):
    if request is None:
        qs = QueryDict().copy()
    else:
        qs = request.GET.copy()
    # Can't use update() here as it would just append to the querystring
    for k, v in kwargs.items():
        qs[k] = v
    return qs.urlencode()
