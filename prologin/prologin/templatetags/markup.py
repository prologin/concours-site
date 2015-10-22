from django import template
from django.utils.text import mark_safe

import markdown as markdown_lib
import pygments
import pygments.lexers
import pygments.formatters

register = template.Library()


def _init_flavored_markdown():
    import markdown.extensions.codehilite
    import markdown.extensions.fenced_code
    import markdown.extensions.footnotes
    from prologin.utils.markdown.emoji import EmojiExtension
    from prologin.utils.markdown.nofollow import NofollowExtension
    ext = [
        markdown.extensions.footnotes.FootnoteExtension(),
        markdown.extensions.codehilite.CodeHiliteExtension(linenums=True, css_class="pyg-hl"),
        'markdown.extensions.fenced_code',
        EmojiExtension(),
        NofollowExtension(),
    ]
    return markdown_lib.Markdown(extensions=ext, safe_mode='escape', output_format='html5')

flavored_markdown_converter = _init_flavored_markdown()


@register.filter
def markdown(value):
    return mark_safe(markdown_lib.markdown(value))


@register.filter
def flavored_markdown(value):
    rendered = mark_safe(flavored_markdown_converter.convert(value))
    flavored_markdown_converter.reset()
    return rendered


@register.simple_tag
def pygmentize(code, language, **options):
    lexer = pygments.lexers.get_lexer_by_name(language)
    formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass="pyg-hl", **options)
    return mark_safe(pygments.highlight(code, lexer, formatter))
