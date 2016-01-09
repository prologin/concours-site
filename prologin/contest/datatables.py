import datatableview
from datatableview import Datatable
from django.core.urlresolvers import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

import contest.models


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
    correction_url_name = 'correction-contestant-qualification'

    assigned_event = datatableview.TextColumn(_("Assigned semifinal"),
                                              sources=['assignation_semifinal_event__center__name',
                                                       'assignation_semifinal_event__center__city'],
                                              processor='get_assignation_semifinal_event')
    score = datatableview.IntegerColumn(_("Score"), source='score_for_qualification')

    def __init__(self, object_list, url, **kwargs):
        super().__init__(object_list, url, **kwargs)
        self.set_column_order('user', 'assigned_event')

    def get_assignation_semifinal_event(self, contestant, **kwargs):
        event = contestant.assignation_semifinal_event
        if event:
            return format_html('{} <small class="text-muted">{}</small>',
                               event.center.name,
                               date_format(event.date_begin, 'SHORT_DATE_FORMAT'))
        return format_html('{} <small class="text-muted">({} correction(s))</small>',
                           contest.models.Assignation(contestant.assignation_semifinal).name.title(),
                           contestant.corrections.count())



class ContestantSemifinalTable(AbstractContestantTable):
    event_type = contest.models.Event.Type.semifinal
    correction_url_name = 'correction-contestant-semifinal'

    score = datatableview.IntegerColumn(_("Score"), source='score_for_semifinal')
