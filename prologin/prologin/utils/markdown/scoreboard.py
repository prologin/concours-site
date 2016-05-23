import re
from django.template.loader import get_template
from markdown import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree


class ScoreboardProcessor(BlockProcessor):
    PATTERN = re.compile(r'\{%\s+scoreboard(?:\s+(?P<type>before|after)\s+(?P<n>[0-9]+))?\s+%\}')

    def __init__(self, parser, scoreboard):
        super().__init__(parser)
        self.scoreboard = scoreboard

    def test(self, parent, block):
        test = self.PATTERN.match(block)
        return test is not None

    def run(self, parent, blocks):
        match = self.PATTERN.match(blocks.pop(0))
        type = match.group('type')
        start = None
        end = None
        if type is not None:
            n = int(match.group('n'))
            if type == 'before':
                end = n
            elif type == 'after':
                start = n
            else:
                return
        scoreboard = etree.SubElement(parent, 'div', {'class': 'scoreboard'})
        scoreboard.text = get_template('archives/inline-scoreboard.html').render({
            'scoreboard': self.scoreboard[start:end],
            'scoreboard_start': 1 if start is None else start + 1,
            'scoreboard_end': end or len(self.scoreboard),
        })


class ScoreboardExtension(Extension):
    def __init__(self, scoreboard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scoreboard = scoreboard

    def extendMarkdown(self, md, md_globals):
        """ Add an instance of ScoreboardProcessor to BlockParser. """
        md.parser.blockprocessors.add('scoreboard', ScoreboardProcessor(md.parser, self.scoreboard), '<hashheader')


def makeExtension(*args, **kwargs):
    return ScoreboardExtension(*args, **kwargs)
