from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def conflose_css(user):
    if not user or not hasattr(user, 'userconflose'):
        return ''
    userconflose = user.userconflose
    css = userconflose.conflose.css.replace('%%message%%',
                                            userconflose.message)
    return mark_safe('<style>{}</style>'.format(css))
