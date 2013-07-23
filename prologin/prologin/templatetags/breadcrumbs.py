from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.html import escape

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

    def real_value(self, var, context):
        """Return the real value based on the context."""
        try:
            real_var = var.resolve(context)
        except (VariableDoesNotExist):
            real_var = str(var)
        return escape(real_var)

    def getUrl(self, params):
        ret = None
        if len(params) > 1:
            ret = reverse(params[0], args=params[1:])
        else:
            ret = reverse(params[0]) if params[0] != 'none' else None
        return ret
        
    def render(self, context):
        title = self.real_value(self.title, context)

        if self.url:
            params = []
            for el in self.url:
                params.append(self.real_value(el, context))
            url = self.getUrl(params)
            if url != None:
                crumb = '<li><a href="%s">%s</a> <span class="divider">&gt;</span></li>' % (url, title)
            else :
                crumb = '<li>%s <span class="divider">&gt;</span></li>' % title
        else:
            crumb = '<li class="active">%s</li>' % title
        return crumb