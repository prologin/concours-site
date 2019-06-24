# Copyright (C) <2016> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from datetime import timedelta
from django import template

register = template.Library()

@register.filter()
def add_days(inp, days):
    return inp + timedelta(days=days)
