from django import template
from django.utils.encoding import force_text
from documents.models import latex_escape

register = template.Library()


@register.filter()
def escapetex(input):
    return latex_escape(force_text(input))


@register.filter()
def nonempty(input):
    if not input:
        return "~"
    return input
