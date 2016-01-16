from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import contest.models
import contest.widgets


class EventWishList(forms.ModelMultipleChoiceField):
    """
    Custom field & widget to display a read-only, sorted list of event wishes (as a <ol>).
    """

    class Widget(forms.widgets.SelectMultiple):
        def render(self, name, value, attrs=None, choices=()):
            # reimplemented to use a <ol>
            if value is None:
                value = []
            output = ['<ol class="event-wish-list">']
            options = self.render_options(choices, value)
            if options:
                output.append(options)
            output.append('</ol>')
            return mark_safe('\n'.join(output))

        def render_options(self, choices, selected_choices):
            # reimplemented to keep ordering from selected_choices
            choices = [(pk, obj) for pk, obj in self.choices if pk in selected_choices]
            choices.sort(key=lambda pair: selected_choices.index(pair[0]))
            output = []
            for option_value, option_label in choices:
                output.append(self.render_option(selected_choices, option_value, option_label))
            return '\n'.join(output)

        def render_option(self, selected_choices, option_value, option_label):
            # reimplemented to use a <li> and short_description
            return format_html('<li data-event-id="{}">{}</li>', option_label.pk, option_label.short_description)

    widget = Widget

    def label_from_instance(self, obj):
        return obj


class ContestantCorrectionForm(forms.ModelForm):
    """
    Abstract form for ContestantQualificationForm and ContestantSemifinalForm.
    """
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3,
                                                           'placeholder': _("A reason for your changes and/or a "
                                                                            "comment about the submission")}),
                              required=False,
                              label=_("Changelog comment"))

    class Meta:
        model = contest.models.Contestant
        fields = ()

    @property
    def contestant(self):
        return self.instance


class ContestantQualificationForm(ContestantCorrectionForm):
    class Meta(ContestantCorrectionForm.Meta):
        fields = ('score_qualif_qcm',
                  'score_qualif_algo',
                  'score_qualif_bonus',
                  'assignation_semifinal_wishes',
                  'assignation_semifinal',
                  'assignation_semifinal_event',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict the event queryset to this edition semifinals
        qs = (self.fields['assignation_semifinal_event'].queryset
              .filter(edition=self.contestant.edition, type=contest.models.Event.Type.semifinal.value))
        self.fields['assignation_semifinal_event'] = contest.widgets.EventWishModelChoiceField(
            label=self.Meta.model._meta.get_field('assignation_semifinal_event').verbose_name,
            required=False, queryset=qs, empty_label=_("Unassigned"))

        # Custom field to display the event wishes read-only
        qs = (self.fields['assignation_semifinal_wishes'].queryset
              .select_related('center')
              .filter(edition=self.contestant.edition, type=contest.models.Event.Type.semifinal.value))
        self.fields['assignation_semifinal_wishes'] = EventWishList(queryset=qs, required=False)
        if self.contestant:
            # FIXME: figure why we have to do the ordering manually
            self.initial['assignation_semifinal_wishes'] = list(self.contestant.assignation_semifinal_wishes
                                                                .select_related('eventwish')
                                                                .order_by('eventwish__order')
                                                                .values_list('pk', flat=True))

    def clean(self):
        clean_data = super().clean()
        del clean_data['assignation_semifinal_wishes']
        assigned = clean_data['assignation_semifinal']
        if assigned != contest.models.Assignation.assigned.value:
            clean_data['assignation_semifinal_event'] = None
        elif not clean_data['assignation_semifinal_event']:
            raise forms.ValidationError(_("Semifinal assignation event is required if contestant is assigned."))


class ContestantSemifinalForm(ContestantCorrectionForm):
    class Meta(ContestantCorrectionForm.Meta):
        fields = ('score_semifinal_written',
                  'score_semifinal_interview',
                  'score_semifinal_machine',
                  'score_semifinal_bonus',
                  'assignation_final',)
