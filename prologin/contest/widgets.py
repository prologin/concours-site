from django import forms
from django.utils import formats
from django.utils.encoding import force_text
from django.utils.html import format_html_join, format_html
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
    """
    Custom implementation of a Select to add data-name and data-addr to each rendered <option/>.
    Uses Django's internals. May break with future Django releases.
    """
    def render_option(self, selected_choices, option_value, option_label):
        # BEGIN copy-pasted from Django source, because no other way
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        # END
        if option_value:
            center = option_label.center
            date = formats.date_format(option_label.date_begin, "SHORT_DATE_FORMAT")
            addr = "{}, {} {}".format(center.address, center.postal_code, center.city)
            name = "{} — {}".format(date, center.name)
            selected_html = mark_safe(selected_html + format_html(' data-name="{}" data-addr="{}"', name, addr))
            option_label = '{} — {} — {}, {} {}'.format(date, center.name, center.address, center.postal_code, center.city)
        return format_html('<option value="{}"{}>{}</option>', option_value, selected_html, force_text(option_label))


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
