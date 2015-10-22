import markdown as markdown_lib
import pygments
import pygments.lexers
import pygments.formatters

from django import template
from django.utils.text import mark_safe

register = template.Library()


def _init_flavored_markdown():
    import markdown.extensions.codehilite
    import markdown.extensions.fenced_code
    import markdown.extensions.footnotes
    from prologin.utils.markdown.emoji import UnimojiExtension
    ext = [
        markdown.extensions.footnotes.FootnoteExtension(UNIQUE_IDS=False),
        markdown.extensions.codehilite.CodeHiliteExtension(linenums=True, css_class="pyg-hl"),
        'markdown.extensions.fenced_code',
        UnimojiExtension(),
    ]
    return markdown_lib.Markdown(extensions=ext, safe_mode='escape', output_format='html5')

flavored_markdown_converter = _init_flavored_markdown()


@register.filter
def markdown(value):
    return mark_safe(markdown_lib.markdown(value))


@register.filter
def flavored_markdown(value):
    return mark_safe(flavored_markdown_converter.convert(value))


@register.simple_tag
def pygmentize(code, language, **options):
    lexer = pygments.lexers.get_lexer_by_name(language)
    formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass="pyg-hl", **options)
    return mark_safe(pygments.highlight(code, lexer, formatter))
