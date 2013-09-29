from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape
from menu.models import MenuEntry

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

    def render_entry(self, url, value, class_lst=[]):
        str_classes = ''
        if len(class_lst) > 0:
            str_classes = ' '.join(class_lst)
            str_classes = ' class="%s"' % str_classes
        return '<li%s><a href="%s">%s</a></li>' % (str_classes, url, value)

    def render(self, context):
        ret = ''
        elems = MenuEntry.objects.all().filter(parent__id=None).order_by('position')

        for i in range(len(elems)):
            el = elems[i]
            children = MenuEntry.objects.all().filter(parent__id=el.id).order_by('position')

            if len(children) > 0:
                children_html = ''
                menu_class = 'menu-expanded' if self.tokens[0] == el.slug else 'menu-collapsed'
                for child in children:
                    children_html += self.render_entry(self.real_url(child.url), self.real_value(child.name, context), ['menu-current'] if self.tokens[1] == child.slug else [])
                ret += '<li class="%s"><span class="menu-main-elem">%s</span> <ul class="sub-menu">%s</ul></li>' % (menu_class, self.real_value(el.name, context), children_html)
            else:
                menu_class = ['menu-current'] if self.tokens[0] == el.slug else []
                ret += self.render_entry(self.real_url(el.url), self.real_value(el.name, context), menu_class)
            
        return '<ul id="main-menu">%s</ul>' % ret
