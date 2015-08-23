from django import template
from django.utils.text import mark_safe
from markdown import markdown as markdown_to_html

register = template.Library()


@register.filter
def markdown(value):
    return mark_safe(markdown_to_html(value))
