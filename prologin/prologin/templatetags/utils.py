from django import template
from django.conf import settings

register = template.Library()

@register.filter
def percentage_to_max(num, max):
    return int(num / max * 100)


@register.filter
def choiceenum_label(enum_member):
    return enum_member.__class__.label_for(enum_member)


@register.filter
def phone_number(num):
    """
    Formats a French phone number: space separated groups of two digits.
    Starts from the end, such that we do not care if it starts like +336, 06, or 6.
    :param num: the phone number to format
    :rtype sting
    """
    num = [c for c in num.strip()[::-1] if not c.isspace()]
    if len(num) % 2 == 1:
        # so zip() does not truncate to min length
        num.append('')
    return '\u00A0'.join(a + b for a, b in zip(num[-1::-2], num[-2::-2]))


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
