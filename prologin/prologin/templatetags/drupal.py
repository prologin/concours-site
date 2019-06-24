# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django import template
from django.utils.safestring import mark_safe
register = template.Library()


@register.filter
def drupaltpl(template):
    return mark_safe(template)
