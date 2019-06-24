# Copyright (C) <2013> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.utils.html import linebreaks
from zinnia.markups import markdown
from zinnia.markups import restructuredtext
from zinnia.markups import textile
from zinnia.models_bases.entry import AbstractEntry
from zinnia.settings import MARKUP_LANGUAGE


class NewsEntry(AbstractEntry):
    """
    Represents a news entry.
    """

    # The default Zinnia implementation of this does stupid content sniffing,
    # assuming that if something contains </p> it is raw HTML. That's not true,
    # since Markdown can contain HTML.
    @property
    def html_content(self):
        """
        Returns the "content" field formatted in HTML.
        """
        if MARKUP_LANGUAGE == 'markdown':
            return markdown(self.content)
        elif MARKUP_LANGUAGE == 'textile':
            return textile(self.content)
        elif MARKUP_LANGUAGE == 'restructuredtext':
            return restructuredtext(self.content)
        return linebreaks(self.content)

    class Meta(AbstractEntry.Meta):
        abstract = True
