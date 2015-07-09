from django import template
from django.utils.text import mark_safe
register = template.Library()


@register.filter
def drupaltpl(template):
    return mark_safe(template)
