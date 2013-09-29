from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape
from menu.models import MenuEntry
from prologin.utils import real_value, get_real_url

register = template.Library()

@register.tag
def menu(parser, token):
    """
    How to use this tag: {% menu [slug ...] %}

    Examples:
    {% menu %}
    {% menu l_association %}
    """
    return MenuNode(token.split_contents()[1:])

class MenuNode(Node):
    def __init__(self, tokens):
        self.tokens = tokens + [None for _ in range(3 - len(tokens))]

    def render_entry(self, url, value, class_lst=[]):
        str_classes = ''
        if len(class_lst) > 0:
            str_classes = ' '.join(class_lst)
            str_classes = ' class="%s"' % str_classes
        return '<li%s><a href="%s">%s</a></li>' % (str_classes, url, value)

    def if_access(self, entry, context):
        assoc = {
            'all': lambda req : True,
            'guest': lambda req : not req.user.is_authenticated(),
            'logged': lambda req : req.user.is_authenticated(),
            'admin': lambda req : req.user.is_staff,
            }
        return assoc[entry.access](context['request'])

    def render(self, context):
        ret = ''
        elems = MenuEntry.objects.all().filter(parent__id=None).order_by('position')

        for i in range(len(elems)):
            el = elems[i]
            if not self.if_access(el, context):
                continue

            children = MenuEntry.objects.all().filter(parent__id=el.id).order_by('position')

            if len(children) > 0:
                children_html = ''
                menu_class = 'menu-expanded' if real_value(self.tokens[0], context) == el.slug else 'menu-collapsed'
                for child in children:
                    if not self.if_access(child, context):
                        continue
                    children_html += self.render_entry(get_real_url(child.url), real_value(child.name, context), ['menu-current'] if real_value(self.tokens[1], context) == child.slug else [])
                ret += '<li class="%s"><span class="menu-main-elem">%s</span> <ul class="sub-menu">%s</ul></li>' % (menu_class, real_value(el.name, context), children_html)
            else:
                menu_class = ['menu-current'] if self.tokens[0] == el.slug else []
                ret += self.render_entry(get_real_url(el.url), real_value(el.name, context), menu_class)
            
        return '<ul id="main-menu">%s</ul>' % ret
