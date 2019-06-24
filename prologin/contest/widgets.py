# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django import forms
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ungettext
from itertools import zip_longest
from collections import OrderedDict

"""
This implements EventWishChoiceField. To this end, it needs three more subclasses of Django form fields/widgets.
"""

CHOICE_NAMES = (_("First choice"), _("Second choice"), _("Third choice"))


class EventWishChoiceFieldWidget(forms.widgets.MultiWidget):
    """
    Custom implementation of MultiWidget that display 'First choice', etc. and the sub-fields from the underlying
    MultiValueField.
    """
    def __init__(self, fields, attrs=None):
        super().__init__([field.widget for field in fields], attrs)

    def decompress(self, value):
        if value:
            return [int(pk) for pk in value.split(',')]
        return [None] * len(self.widgets)

    def format_output(self, rendered_widgets):
        return format_html_join('', '<span class="event-wish-label">{}</span>{}',
                                ((name, mark_safe(widget))
                                 for name, widget in zip_longest(CHOICE_NAMES, rendered_widgets, fillvalue=_("Choice"))))


class EventWishSelect(forms.widgets.Select):
    option_template_name = 'contest/school-select-option.html'


class EventWishModelChoiceField(forms.ModelChoiceField):
    """
    Custom implementation to use EventWishSelect and pass the raw Event instance to widget.
    """
    widget = EventWishSelect

    def label_from_instance(self, obj):
        # return the raw instance so we can use its attributes in EventWishSelect.render_option
        return obj


class EventWishChoiceField(forms.MultiValueField):
    """
    Custom implementation of MultiValueField that displays max_count EventWishModelChoiceFields and requires at least
    min_count fields to be non-null.
    """
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        self._min_choices = kwargs.pop('min_choices')
        self._max_choices = kwargs.pop('max_choices')
        kwargs['required'] = False  # handled by min_choices/max_choices
        # FIXME: `queryset` is queried `max_choices` times, because of underlying ModelChoiceField implementation
        fields = [
            EventWishModelChoiceField(queryset, required=False, empty_label='')
            for n in range(self._max_choices)
        ]
        widget = EventWishChoiceFieldWidget(fields, attrs={'class': 'event-wish-select form-control'})
        super().__init__(widget=widget, fields=fields, require_all_fields=False, *args, **kwargs)

    def clean(self, value):
        events = super().clean(value)
        events = list(OrderedDict((event, None) for event in events if event).keys())
        if len(events) < self._min_choices:
            raise forms.ValidationError(ungettext("You must provide at least %(count)d choice.",
                                                  "You must provide at least %(count)d choices.",
                                                  self._min_choices) % {'count': self._min_choices})
        return events

    def compress(self, data_list):
        return data_list
