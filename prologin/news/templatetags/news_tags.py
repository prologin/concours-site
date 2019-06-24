# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.template import Library
register = Library()

from django.utils.translation import ugettext as _
from zinnia.templatetags.zinnia import zinnia_breadcrumbs


@register.simple_tag(takes_context=True)
def get_zinnia_breadcrumbs(context):
    return zinnia_breadcrumbs(context, _("News"))['breadcrumbs']
