from datetime import timedelta
from django import template

register = template.Library()

@register.filter()
def add_days(inp, days):
    return inp + timedelta(days=days)
