from markdown import markdown as markdown_to_html
import pygments
import pygments.lexers
import pygments.formatters

from django import template
from django.utils.text import mark_safe

from prologin.utils import Markdown

register = template.Library()


@register.filter
def markdown(value):
    return mark_safe(markdown_to_html(value))


@register.filter
def flavored_markdown(value):
    return mark_safe(Markdown(escape=True)(value))


@register.simple_tag
def pygmentize(code, language, **options):
    lexer = pygments.lexers.get_lexer_by_name(language)
    formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass="pyg-hl", **options)
    return mark_safe(pygments.highlight(code, lexer, formatter))
