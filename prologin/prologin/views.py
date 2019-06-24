# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.core.exceptions import ImproperlyConfigured


class ChoiceGetAttrsMixin(object):
    """
    Mixin that handles a list of GET attributes that can be user-set to a predefined list of valid choices.
    Handles validation and fallback. User class has to use get_clean_attr('name') to access validated attributes.

    The list of attributes is get_attrs; you can also implement get_get_attrs().
    The first item of the choice list will be the default. You can use the None literal.

    Usage:

        class MyView(ChoiceGetAttrsMixin, View):
            get_attrs = {'sort': ['name', 'age', 'city'],
                         'order': ['asc', 'desc']}

            def some_method(self):
                sort = self.get_clean_attr('sort')
                ...
    """

    get_attrs = {}

    def get_get_attr(self):
        return self.get_attrs

    def get_clean_attr(self, attr):
        attrs = self.get_get_attr()
        try:
            choices = attrs[attr]
        except KeyError:
            raise KeyError("{} is not defined in get_attrs".format(attr))
        choices = list(choices)
        try:
            fallback = choices[0]
        except IndexError:
            raise ImproperlyConfigured("Attribute {} has an empty choice list".format(attr))
        value = self.request.GET.get(attr, fallback)
        if value not in choices:
            value = fallback
        return value
