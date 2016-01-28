from django.http import Http404
from django.views.generic import TemplateView

import archives.models
from contest.models import Event


class Index(TemplateView):
    template_name = 'archives/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['archives'] = sorted(archives.models.Archive.all_archives(), reverse=True)
        for archive in context['archives']:
            archive.user = self.request.user
        return context


class SingleArchiveMixin:
    year_field = 'year'
    type_field = 'type'

    def get_archive(self) -> (archives.models.Archive, Event.Type):
        try:
            year = int(self.kwargs[self.year_field])
            event_type = Event.Type[self.kwargs[self.type_field]]
            return archives.models.Archive.by_year(year), event_type
        except (KeyError, ValueError):
            raise Http404()

    def get_context_data(self, **kwargs):
        archive, event_type = self.get_archive()
        context = {}
        context.update(kwargs)
        context['archive'] = archive
        context['event_type'] = event_type
        return super().get_context_data(**context)


class Report(SingleArchiveMixin, TemplateView):
    template_name = 'archives/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attr = 'semifinal' if context['event_type'] is Event.Type.semifinal else 'final'
        context['content'] = getattr(context['archive'], attr).content
        if not context['content']:
            raise Http404()
        return context


class FinalScoreboard(SingleArchiveMixin, TemplateView):
    template_name = 'archives/finale-scoreboard.html'

    def get(self, request, *args, **kwargs):
        archive, event_type = self.get_archive()
        if not archive.final.scoreboard:
            raise Http404()
        return super().get(request, *args, **kwargs)
