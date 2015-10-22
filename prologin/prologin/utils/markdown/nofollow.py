"""
Nofollow Extension for Python-Markdown
=====================================

Modify the behavior of links in Python-Markdown by adding rel="nofollow" to all generated links.
"""

from markdown import Extension
from markdown.inlinepatterns import (LinkPattern, ReferencePattern, AutolinkPattern, AutomailPattern,
                                     LINK_RE, REFERENCE_RE, SHORT_REF_RE, AUTOLINK_RE, AUTOMAIL_RE)


class NofollowMixin:
    def handleMatch(self, m):
        el = super().handleMatch(m)
        if el is not None:
            el.set('rel', 'nofollow')
        return el


class NofollowLinkPattern(NofollowMixin, LinkPattern):
    pass


class NofollowReferencePattern(NofollowMixin, ReferencePattern):
    pass


class NofollowAutolinkPattern(NofollowMixin, AutolinkPattern):
    pass


class NofollowAutomailPattern(NofollowMixin, AutomailPattern):
    pass


class NofollowExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['link'] = NofollowLinkPattern(LINK_RE, md)
        md.inlinePatterns['reference'] = NofollowReferencePattern(REFERENCE_RE, md)
        md.inlinePatterns['short_reference'] = NofollowReferencePattern(SHORT_REF_RE, md)
        md.inlinePatterns['autolink'] = NofollowAutolinkPattern(AUTOLINK_RE, md)
        md.inlinePatterns['automail'] = NofollowAutomailPattern(AUTOMAIL_RE, md)


def makeExtension(*args, **kwargs):
    return NofollowExtension(*args, **kwargs)
