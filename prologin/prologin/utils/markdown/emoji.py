"""
Unicode Emojis for Python-Markdown
==================================

Converts defined emoticon symbols to image emojis.
"""

from django.contrib.staticfiles.storage import staticfiles_storage

from markdown import Extension
from markdown.util import etree
from markdown.inlinepatterns import Pattern
import os

from .emoji_list import EMOJIS  # generated using assest/update-emojis.py


class EmojiExtension(Extension):
    config = {
        'wrap_char': [
            ':',
            "Character used to wrap the emoticon name.",
        ],
        'span_class': [
            'emoji',
            "A CSS class (default: 'emoji') for the emoticons-encompassing"
            "<span>. Disabled if None."
        ],
    }

    def extendMarkdown(self, md, md_globals):
        import re
        pattern = r'((?<=\s)|(?<=^)){c}(?P<emoticon>{list}){c}(?=\s|$)'.format(
            c=self.getConfig('wrap_char'),
            list='|'.join(map(re.escape, EMOJIS.keys())))
        md.inlinePatterns['emoji'] = EmojiPattern(pattern, md, self)


class EmojiPattern(Pattern):
    def __init__(self, pattern, md, extension):
        super().__init__(pattern, md)
        self.ext = extension

    def handleMatch(self, m):
        # Get the preferred Unicode emoticon, or override
        emoji = m.group('emoticon')
        try:
            image = EMOJIS[emoji] + '.png'
        except KeyError:
            return emoji
        rel_path = os.path.join('img', 'emojis', image).replace('\\', '/')
        path = staticfiles_storage.url(rel_path)
        img = etree.Element('img')
        img.set('src', path)
        img.set('alt', emoji)
        img.set('class', self.ext.getConfig('span_class'))
        return img


def makeExtension(*args, **kwargs):
    return EmojiExtension(*args, **kwargs)
