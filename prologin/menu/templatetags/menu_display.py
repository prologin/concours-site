from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape
from menu.models import MenuEntry

register = template.Library()

@register.tag
def menu(parser, token):
    """
    How to use this tag: {% menu [hid ...] %}

    Examples:
    {% menu %}
    {% menu l_association %}
    """
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
        if url[0] not in ['/', '#'] and url.find('://') == -1:
            args = url.split('|')
            url = args.pop(0)
            ret = reverse(url, args=args)
        return ret

    def render(self, context, parent_id=None):
        elems = MenuEntry.objects.all().filter(parent__id=parent_id).order_by('position')
        ret = ''
        try:
            current_token = self.tokens.pop(0)
        except:
            current_token = None

        for i in range(len(elems)):
            el = elems[i]
            if current_token is not None and current_token == el.hid:
                ret += '<li class="menu-expanded"><a href="%s">%s</a>%s</li>' % (self.real_url(el.url), self.real_value(el.name, context), self.render(context, el.id))
            elif len(MenuEntry.objects.all().filter(parent__id=el.id)) > 0:
                ret += '<li class="menu-collapsed"><a href="%s">%s</a></li>' % (self.real_url(el.url), self.real_value(el.name, context))
            else:
                ret += '<li><a href="%s">%s</a></li>' % (self.real_url(el.url), self.real_value(el.name, context))
        return '<ul class="menu">%s</ul>' % ret
