from django.template import Library
register = Library()

from bs4 import BeautifulSoup
from django.template import defaultfilters
from zinnia.templatetags.zinnia import zinnia_breadcrumbs


@register.filter
def cuthere_excerpt(content):
    try:
        cut_here = BeautifulSoup(content).find('a', id='cuthere')
        return ''.join(map(str, reversed(cut_here.parent.find_previous_siblings())))
    except AttributeError:
        return defaultfilters.truncatewords(content, 100)


@register.assignment_tag(takes_context=True)
def get_zinnia_breadcrumbs(context):
    return zinnia_breadcrumbs(context, "News")['breadcrumbs']
