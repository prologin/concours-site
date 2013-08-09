from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape
from menu.models import MenuEntry

register = template.Library()

@register.tag
def menu(parser, token):
    return MenuNode(token.split_contents()[1:])

class MenuNode(Node):
    def __init__(self, tokens):
        self.tokens = tokens

    def real_value(self, var, context):
        """Return the real value based on the context."""
        try:
            real_var = template.Variable(var).resolve(context)
        except:
            real_var = '%s' % var
        return escape(real_var)

    def real_url(self, url):
        ret = url
        if url[0] not in ['/', '#'] and url[:4] != 'http':
            # TODO: support url parameters
            # TODO: support url parameters resolution
            ret = reverse(url)
        return ret

    def render(self, context, parent_id=None):
        elems = MenuEntry.objects.all().filter(parent__id=parent_id)
        ret = ''
        # TODO: support sub-menu display using tokens
        for i in range(len(elems)):
            el = elems[i]
            ret += '<li><a href="%s">%s</a></li>' % (self.real_url(el.url), self.real_value(el.name, context))
        return '<ul class="menu">%s</ul>' % ret
