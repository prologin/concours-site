import pygments
import pygments.lexers
import pygments.formatters

import mistune


class Renderer(mistune.Renderer):

    def emoji(self, path):
        return '<img class="markdown-emoji" src="{path}">'.format(path=path)

    def mention(self, username, url):
        return '<a class="markdown-mention" href="{url}">@{username}</a>'.format(username=username, url=url)

    def video_link(self, link):
        return '<video controls><source src="{link}"><a href="{link}">{link}</a></video>\n'.format(link=link)

    def youtube(self, video_id):
        return '<span class="markdown-video"><iframe src="https://www.youtube.com/embed/{video_id}?feature=oembed" ' \
               'allowfullscreen></iframe></span>\n'.format(video_id=video_id)

    def vimeo(self, video_id):
        return '<span class="markdown-video"><iframe src="https://player.vimeo.com/video/{video_id}" ' \
               'allowfullscreen></iframe></span>\n'.format(video_id=video_id)

    def block_code(self, code, lang=None):
        code = code.rstrip('\n')
        lexer = pygments.lexers.get_lexer_by_name('text' if lang is None else lang)
        formatter = pygments.formatters.HtmlFormatter(linenos=True, cssclass="pyg-hl")
        return pygments.highlight(code, lexer, formatter)
