import mistune

from .renderer import Renderer
from .block import BlockLexer
from .inline import InlineLexer


class Markdown(mistune.Markdown):
    def __init__(self, renderer=None, inline=None, block=None, **kwargs):
        if renderer is None:
            renderer = Renderer(**kwargs)

        if block is None:
            kwargs['block'] = BlockLexer

        if inline is None:
            kwargs['inline'] = InlineLexer

        super().__init__(renderer=renderer, **kwargs)

    def render(self, text):
        return super().render(text).strip()

    def get_mentions(self):
        return self.inline.mentions

    def parse_video_link(self):
        return self.renderer.video_link(link=self.token['link'])

    def parse_youtube(self):
        return self.renderer.youtube(video_id=self.token['video_id'])

    def parse_vimeo(self):
        return self.renderer.vimeo(video_id=self.token['video_id'])
