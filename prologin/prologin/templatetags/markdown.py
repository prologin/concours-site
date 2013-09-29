from django import template
from django.template import Node, Variable
from django.utils.html import escape
from prologin.utils import real_value
from markdown import markdown as markdown_to_html

register = template.Library()

@register.tag
def markdown(parser, token):
    return MarkdownNode(token.split_contents()[1:])

class MarkdownNode(Node):
    def __init__(self, tokens):
        print(tokens)
        self.content = Variable(tokens[0])

    def render(self, context):
        content = real_value(self.content, context)
        content = markdown_to_html(content)
        return content
