# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import bleach
from django import template
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

import markdown as markdown_lib
import pygments
import pygments.lexers
import pygments.formatters

register = template.Library()

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'p', 'span', 'a', 'em', 'strong', 'del', 'br', 'img', 'hr',
    'ul', 'ol', 'li',
    'dl', 'dd', 'dt',
    'div', 'code', 'pre', 'blockquote', 'input',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th',
]
ALLOWED_ATTRS = ['class', 'rel', 'src', 'alt', 'style', 'href', 'id', 'type', 'checked', 'disabled', 'title']
ALLOWED_STYLES = ['max-width']


def _init_flavored_markdown():
    import markdown.extensions.codehilite
    import markdown.extensions.fenced_code
    import markdown.extensions.tables
    import markdown.extensions.footnotes
    import markdown.extensions.toc
    import markdown.extensions.smart_strong
    import gfm
    from prologin.utils.markdown.nofollow import NofollowExtension
    ext = [
        markdown.extensions.fenced_code.FencedCodeExtension(),
        markdown.extensions.tables.TableExtension(),
        markdown.extensions.footnotes.FootnoteExtension(),
        markdown.extensions.smart_strong.SmartEmphasisExtension(),
        markdown.extensions.codehilite.CodeHiliteExtension(linenums=True, css_class="codehilite"),
        markdown.extensions.toc.TocExtension(slugify=lambda s, _: slugify('bdy-' + s),
                                             permalink=True,
                                             baselevel=1),
        gfm.AutolinkExtension(),
        gfm.AutomailExtension(),
        gfm.SemiSaneListExtension(),
        gfm.SpacedLinkExtension(),
        gfm.StrikethroughExtension(),
        gfm.TaskListExtension(checked=('[x]', '✅', '✓', '✔'), unchecked=('[ ]', '✗', '✘'),
                              item_attrs={'class': 'task-list-item'},
                              checkbox_attrs={'class': 'task-list-item-checkbox'}),
        NofollowExtension(),
    ]
    return markdown_lib.Markdown(extensions=ext, output_format='html5')

flavored_markdown_converter = _init_flavored_markdown()


@register.filter
def markdown(value, escape=True):
    rendered = markdown_lib.markdown(value)
    if escape:
        rendered = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, styles=ALLOWED_STYLES)
    return mark_safe(rendered)


@register.filter
def flavored_markdown(value, escape=True):
    rendered = flavored_markdown_converter.convert(value)
    if escape:
        rendered = bleach.clean(rendered, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, styles=ALLOWED_STYLES)
    flavored_markdown_converter.reset()
    return mark_safe(rendered)


@register.filter
def archive_markdown(value, scoreboard):
    import markdown.extensions.toc
    from prologin.utils.markdown.scoreboard import ScoreboardExtension
    converter = markdown_lib.Markdown(extensions=[
        markdown.extensions.toc.TocExtension(slugify=lambda s, _: slugify('bdy-' + s),
                                             permalink=True,
                                             baselevel=1),
        ScoreboardExtension(scoreboard),
    ], safe_mode=False, output_format='html5')
    rendered = mark_safe(converter.convert(value))
    return rendered


@register.simple_tag
def pygmentize(code, language, **options):
    lexer = pygments.lexers.get_lexer_by_name(language)
    formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass="codehilite", **options)
    return mark_safe(pygments.highlight(code, lexer, formatter))
