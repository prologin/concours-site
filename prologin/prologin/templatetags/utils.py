from django import template
from django.conf import settings

register = template.Library()

# FIXME: in Dango 1.9, the following two tags can be refactored to simple_tag only


@register.simple_tag
def get_setting(name):
    """
    Example usage:
    Contact us at {% get_setting 'CONTACT_EMAIL' %}
    """
    return getattr(settings, name, None)


@register.assignment_tag
def get_setting_var(name):
    """
    Example usage:
    {% get_setting_var 'CONTACT_EMAIL' as email %}
    Contact use at {{ email }}
    """
    return getattr(settings, name, None)


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")

    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()

    return CaptureasNode(nodelist, args)


class CaptureasNode(template.Node):

    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''
