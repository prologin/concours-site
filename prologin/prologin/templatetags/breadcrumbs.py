from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape
from prologin.utils import real_value, get_url

register = template.Library()

@register.tag
def breadcrumb(parser, token):
    return BreadcrumbNode(token.split_contents()[1:])

class BreadcrumbNode(Node):
    def __init__(self, tokens):
        self.title = Variable(tokens[0])
        self.url = None
        if len(tokens) >= 2:
            self.url = []
            for el in tokens[1:]:
                self.url.append(Variable(el))

    def render(self, context):
        title = real_value(self.title, context)

        url = None
        if self.url:
            params = []
            for el in self.url:
                params.append(real_value(el, context))
            url = get_url(params)

        if url != None:
            crumb = '<li><a href="%s">%s</a></li>' % (url, title)
        else :
            crumb = '<li>%s</li>' % title

        return crumb
