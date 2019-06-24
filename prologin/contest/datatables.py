# Copyright (C) <2015> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import datatableview
from datatableview import Datatable
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _, ngettext_lazy

import contest.models
from contest.models import Assignation


class AbstractContestantTable(Datatable):
    event_type = None
    correction_url_name = None

    user = datatableview.TextColumn(_("User"),
                                    sources=['user__username', 'user__first_name', 'user__last_name'],
                                    processor='get_user')
    language = datatableview.TextColumn(_("Programming language"),
                                        source='preferred_language',
                                        processor='get_language')
    actions = datatableview.DisplayColumn("", processor='get_actions', sortable=False)

    class Meta:
        columns = []
        structure_template = 'correction/datatable.html'

    def __init__(self, object_list, url, **kwargs):
        super().__init__(object_list, url, **kwargs)
        # Put actions at the end
        self.columns['actions'] = self.columns.pop('actions')

    def set_column_order(self, *columns):
        popped = [(column, self.columns.pop(column)) for column in columns]
        other_columns = self.columns.copy()
        self.columns.clear()
        for name, column in popped:
            self.columns[name] = column
        self.columns.update(other_columns)

    def get_user(self, contestant, **kwargs):
        user = contestant.user
        return format_html('{} <small class="text-muted">{}</small>',
                           user.username, user.get_full_name())

    def get_language(self, contestant, **kwargs):
        return contestant.get_preferred_language_display() if contestant.preferred_language else ""

    def correct_link(self, contestant):
        return format_html('<a href="{}" class="btn btn-default btn-xs"><i class="fa fa-wrench"></i> {}</a>',
                           reverse('contest:{}'.format(self.correction_url_name),
                                   kwargs={'year': contestant.edition.year, 'cid': contestant.pk}),
                           _("Correct"))
    def get_extra_actions(self, contestant):
        return []

    def get_actions(self, contestant, **kwargs):
        actions = self.get_extra_actions(contestant)
        actions.append(self.correct_link(contestant))
        return ' '.join(actions)


class ContestantQualificationTable(AbstractContestantTable):
    event_type = contest.models.Event.Type.qualification
    correction_url_name = 'correction:contestant-qualification'

    assigned_event = datatableview.TextColumn(_("Assigned regional event"),
                                              sources=['assignation_semifinal_event__center__name',
                                                       'assignation_semifinal_event__center__city'],
                                              processor='get_assignation_semifinal_event')
    assignation_status = datatableview.TextColumn(_("Assignation status"),
                                                  sources='assignation_semifinal',
                                                  processor='get_assignation_semifinal_status')
    score = datatableview.IntegerColumn(_("Score"), source='score_for_qualification')

    def __init__(self, object_list, url, **kwargs):
        super().__init__(object_list, url, **kwargs)
        self.set_column_order('user', 'assigned_event')

    def get_assignation_semifinal_event(self, contestant, **kwargs):
        event = contestant.assignation_semifinal_event
        if not event:
            return ''
        return format_html('{} <small class="text-muted">{}</small>',
                           event.center.name,
                           date_format(event.date_begin, 'SHORT_DATE_FORMAT'))

    def get_assignation_semifinal_status(self, contestant, **kwargs):
        count = contestant.corrections.filter(event_type=self.event_type.value).count()
        corrections = ngettext_lazy("%(count)d correction", "%(count)d corrections", count) % {'count': count}
        return format_html('{} <small class="text-muted"> - {}</small>',
                           Assignation.label_for(Assignation(contestant.assignation_semifinal)),
                           corrections)

    def convocation_link(self, contestant):
        if contestant.assignation_semifinal == contest.models.Assignation.assigned.value:
            return format_html('<a href="{}" class="btn btn-default btn-xs"><i class="fa fa-graduation-cap"></i> {}</a>',
                               reverse('documents:semifinal:contestant-convocation',
                                       kwargs={'year': contestant.edition.year, 'contestant': contestant.pk}),
                               _("Convocation"))
        else:
            return format_html('<span class="btn btn-default btn-xs disabled" title="{}">'
                               '<i class="fa fa-graduation-cap"></i> {}</span>',
                               _("Contestant is not assigned"), _("Convocation"))

    def get_extra_actions(self, contestant):
        return [self.convocation_link(contestant)]


class ContestantSemifinalTable(AbstractContestantTable):
    event_type = contest.models.Event.Type.semifinal
    correction_url_name = 'correction:contestant-semifinal'

    assignation_status = datatableview.TextColumn(_("Assignation status"),
                                                  sources='assignation_final',
                                                  processor='get_assignation_final_status')
    score = datatableview.IntegerColumn(_("Score"), source='score_for_semifinal')

    def get_assignation_final_status(self, contestant, **kwargs):
        count = contestant.corrections.filter(event_type=self.event_type.value).count()
        corrections = ngettext_lazy("%(count)d correction", "%(count)d corrections", count) % {'count': count}
        return format_html('{} <small class="text-muted"> - {}</small>',
                           Assignation.label_for(Assignation(contestant.assignation_final)),
                           corrections)

    def convocation_link(self, contestant):
        if contestant.assignation_final == contest.models.Assignation.assigned.value:
            return format_html('<a href="{}" class="btn btn-default btn-xs"><i class="fa fa-graduation-cap"></i> {}</a>',
                               reverse('documents:final:contestant-convocation',
                                       kwargs={'year': contestant.edition.year, 'contestant': contestant.pk}),
                               _("Convocation"))
        else:
            return format_html('<span class="btn btn-default btn-xs disabled" title="{}">'
                               '<i class="fa fa-graduation-cap"></i> {}</span>',
                               _("Contestant is not assigned"), _("Convocation"))

    def get_extra_actions(self, contestant):
        return [self.convocation_link(contestant)]


class ContestantFinalTable(AbstractContestantTable):
    event_type = contest.models.Event.Type.semifinal
    correction_url_name = 'correction:contestant-semifinal'

    assigned_event = datatableview.TextColumn(_("Assigned regional event"),
                                              sources=['assignation_semifinal_event__center__name',
                                                       'assignation_semifinal_event__center__city'],
                                              processor='get_assignation_semifinal_event')
    assignation_status = datatableview.TextColumn(_("Assignation status"),
                                                  sources='assignation_final',
                                                  processor='get_assignation_final_status')
    score = datatableview.IntegerColumn(_("Score"), source='score_for_semifinal')

    def get_assignation_semifinal_event(self, contestant, **kwargs):
        event = contestant.assignation_semifinal_event
        if not event:
            return ''
        return format_html('{} <small class="text-muted">{}</small>',
                           event.center.name,
                           date_format(event.date_begin, 'SHORT_DATE_FORMAT'))

    def get_assignation_final_status(self, contestant, **kwargs):
        count = contestant.corrections.filter(event_type=self.event_type.value).count()
        corrections = ngettext_lazy("%(count)d correction", "%(count)d corrections", count) % {'count': count}
        return format_html('{} <small class="text-muted"> - {}</small>',
                           Assignation.label_for(Assignation(contestant.assignation_final)),
                           corrections)

    def convocation_link(self, contestant):
        if contestant.assignation_final == contest.models.Assignation.assigned.value:
            return format_html('<a href="{}" class="btn btn-default btn-xs"><i class="fa fa-graduation-cap"></i> {}</a>',
                               reverse('documents:final:contestant-convocation',
                                       kwargs={'year': contestant.edition.year, 'contestant': contestant.pk}),
                               _("Convocation"))
        else:
            return format_html('<span class="btn btn-default btn-xs disabled" title="{}">'
                               '<i class="fa fa-graduation-cap"></i> {}</span>',
                               _("Contestant is not assigned"), _("Convocation"))

    def get_extra_actions(self, contestant):
        return [self.convocation_link(contestant)]
