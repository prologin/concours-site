from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse


register = template.Library()

@register.tag
def root_url(parser, token):
    return RootUrlNode(token.split_contents()[1:])

class RootUrlNode(Node):
    def __init__(self, tokens):
        try:
            self.url = reverse(tokens[0], args=tokens[1:])
        except:
            self.url = None

    def render(self, context):
        ret = ''
        if self.url != None:
            request = context['request']
            ret = request.build_absolute_uri(self.url)
        return ret
