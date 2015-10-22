"""
Unicode Emojis for Python-Markdown
==================================

Converts defined emoticon symbols to Unicode emojis, supported on a
variety of devices [1].

[1]: http://apps.timwhitlock.info/emoji/tables/unicode#block-1-emoticons
"""

from markdown import Extension
from markdown.util import etree
from markdown.inlinepatterns import Pattern


class UnimojiExtension(Extension):
    EMOJI = {
        '😊': ':) :-) :] :-] =) =] ^^ ^_^ ☺'.split(),
        '😉': ';) ;-) ;] ;-]'.split(),
        '😄': ':D :-D =D'.split(),
        '😂': ":,D :'D =,D ='D".split(),
        '😆': 'xD XD'.split(),
        '😛': ':p :-p :P :-P =p =P'.split(),
        '😜': ';p ;-p ;P ;-P'.split(),
        '😏': ':> :->'.split(),
        '😞': ':( :-( ;( ;-( =( =[ ☹'.split(),
        '😣': 'x( X('.split(),
        '😢': ":,( :'( =,( ='(".split(),
        '😠': '>:( >=('.split(),
        '😲': ':O :-O 8-O =O'.split(),
        '😵': 'x-O X-O'.split(),
        '😳': ':$ :-$ :">'.split(),
        '😴': ':zzz:'.split(),
        '😓': ':-X :X :-# :# :-& :&'.split(),
        '😇': 'O:) O:-)'.split(),
        '😈': '3:) 3:-) >:) >:-) >;) >;-)'.split(),
        '😎': '8)'.split(),
        '😖': ':s :-s :S :-S'.split(),
        '😒': ':/ :-/ :\\ :-\\ =/ =\\ :L'.split(),
        '😚': ':* :-*'.split(),
        '😘': ';* ;-*'.split(),
        '❤': '<3'.split(),
        '💔': '</3'.split(),
        '👍': ':y: :Y: :+1:'.split(),
        '👎': ':n: :N: :-1:'.split(),
        '🙌': '\\o/'.split(),
        '🍰': ':cake:'.split(),
        '😸': ':^) :} :-} :3 :-3'.split(),
        '😺': ':^D =^D'.split(),
        '😿': ':^( :{'.split(),
    }
    STYLES = {
        '❤': 'color:red',
        '💔': 'color:red',
        '🍰': 'color:maroon',
    }
    config = {
        'emoji': [
            EMOJI,
            'A mapping from emoticon symbols to a list of aliases.'
        ],
        'styles': [
            STYLES,
            'A mapping from emoticon symbol to a CSS style string. '
            'Only works if span_class is enabled.'
        ],
        'span_class': [
            'emoji',
            'A CSS class (default: "emoji") for the emoticons-encompassing'
            '<span>. Disabled if None.'
        ],
    }

    def __init__(self, *args, **kwargs):
        super(UnimojiExtension, self).__init__(*args, **kwargs)
        # Set keys as aliases so they get processed the same
        for k, v in self.getConfig('emoji').items():
            v.append(k)
        # Inverse the emoji mapping
        aliases = {}
        for emoticon, alias in self.getConfig('emoji').items():
            for a in alias:
                aliases[a] = emoticon
        self.config['aliases'] = [aliases, '']

    def extendMarkdown(self, md, md_globals):
        import re
        pattern = r'((?<=\s)|(?<=^))(?P<emoticon>%s)(?=\s|$)' % '|'.join(map(re.escape, self.getConfig('aliases')))
        md.inlinePatterns['emoji'] = UnimojiPattern(pattern, md, self)


class UnimojiPattern(Pattern):
    def __init__(self, pattern, md, extension):
        super(UnimojiPattern, self).__init__(pattern, md)
        self.ext = extension

    def handleMatch(self, m):
        # Get the preferred Unicode emoticon, or override
        emoticon = self.ext.getConfig('aliases')[m.group('emoticon')]
        # Try to parse it as HTML in case it's overridden
        try:
            element = etree.fromstring(emoticon.encode('utf-8'))
        except etree.ParseError:
            element = None
        # Apply class name if needed
        span_class = self.ext.getConfig('span_class')
        if span_class:
            if element is None:
                element = etree.Element('span')
                element.text = emoticon
            element.set('class', span_class)
            # Apply style formatting
            style = self.ext.getConfig('styles').get(emoticon)
            if style:
                element.set('style', style)
        if element is None:
            return emoticon
        return element


def makeExtension(*args, **kwargs):
    return UnimojiExtension(*args, **kwargs)
