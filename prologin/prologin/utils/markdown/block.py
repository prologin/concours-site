import re

import mistune


class BlockGrammar(mistune.BlockGrammar):
    video_link = re.compile(
        r'^https?://[^\s]+\.(mov|mp4|webm|ogv)'
        r'(\?[^\s]+)?'
        r'(?:\n+|$)'
    )

    # Try to get the video ID. Works for URLs of the form:
    # * https://www.youtube.com/watch?v=Z0UISCEe52Y
    # * http://youtu.be/afyK1HSFfgw
    # * https://www.youtube.com/embed/vsF0K3Ou1v0
    youtube = re.compile(
        r'^https?://(www\.)?'
        r'(youtube\.com/watch\?v='
        r'|youtu\.be/'
        r'|youtube\.com/embed/)'
        r'(?P<id>[a-zA-Z0-9_\-]{11})'
        r'(?:\n+|$)'
    )

    # Try to get the video ID. Works for URLs of the form:
    # * https://vimeo.com/11111111
    # * https://www.vimeo.com/11111111
    # * https://player.vimeo.com/video/11111111
    # * https://vimeo.com/channels/11111111
    # * https://vimeo.com/groups/name/videos/11111111
    # * https://vimeo.com/album/2222222/video/11111111
    # * https://vimeo.com/11111111?param=value
    vimeo = re.compile(
        r'^https?://(www\.|player\.)?'
        r'vimeo\.com/'
        r'(channels/'
        r'|groups/[^/]+/videos/'
        r'|album/(\d+)/video/'
        r'|video/)?'
        r'(?P<id>\d+)'
        r'(\?[^\s]+)?'
        r'(?:\n+|$)'
    )


class BlockLexer(mistune.BlockLexer):
    default_rules = ['video_link', 'youtube', 'vimeo'] + mistune.BlockLexer.default_rules

    def __init__(self, rules=None, **kwargs):
        if rules is None:
            rules = BlockGrammar()

        super(BlockLexer, self).__init__(rules=rules, **kwargs)

    def parse_video_link(self, m):
        link = mistune.escape(m.group(0).strip(), quote=True)
        self.tokens.append({'type': 'video_link', 'link': link})

    def parse_youtube(self, m):
        self.tokens.append({'type': 'youtube', 'video_id': m.group("id")})

    def parse_vimeo(self, m):
        self.tokens.append({'type': 'vimeo', 'video_id': m.group("id")})
