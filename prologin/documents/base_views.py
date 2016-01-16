import collections
from django.conf import settings
from django.http.response import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from rules.contrib.views import PermissionRequiredMixin

import contest.models
import documents.models
import prologin.utils

USER_LIST_ORDERING = ('user__last_name', 'user__first_name')


class BasePDFDocumentView(TemplateView):
    """
    Base view that handles the TeX generation.
    """
    content_type = 'application/pdf'
    pdf_title = 'document'
    filename = 'document'
    extension = '.pdf'

    @staticmethod
    def escape_filename(filename):
        # quick safeguard, nothing inherently safe/secure, because it's shit: http://greenbytes.de/tech/tc2231/
        return filename.replace('"', '_')

    def apply_headers(self, response):
        filename = self.escape_filename(self.get_filename())
        disposition = 'attachment; ' if self.request.GET.get('dl') is not None else ''
        response['Content-Disposition'] = '{}filename="{}"'.format(disposition, filename)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_extra_context())
        return context

    def render_to_response(self, context, **response_kwargs):
        context['pdf_title'] = self.get_pdf_title()
        try:
            with documents.models.generate_tex_pdf(self.get_template_names()[0], context) as output:
                response = HttpResponse(content=open(output, 'rb'), content_type=self.content_type)
                self.apply_headers(response)
                return response
        except prologin.utils.SubprocessFailedException as error:
            if self.can_display_tex_errors():
                # Custom 500 error with stdout/stderr
                return self.response_class(self.request,
                                           template='documents/tex-error-debug.html',
                                           context={'error': error},
                                           status=500)
            return HttpResponseServerError()

    def can_display_tex_errors(self) -> bool:
        """
        Whetere the use can see the TeX generation output.
        Warning: security hazard.
        """
        return self.request.user.has_perm('documents.view_tex_errors')

    def get_pdf_title(self) -> str:
        """
        Override to customize the PDF title (meta-property of the file itself, read by PDF readers).
        """
        return self.pdf_title % self.i18nargs()

    def get_filename(self) -> str:
        """
        Override to customize the file name of the generated PDF file, as displayed in the browser's file save dialog.
        """
        return self.filename % {k: slugify(v) for k, v in self.i18nargs().items()} + self.extension

    def i18nargs(self) -> dict:
        """
        Override to customize the context catalogue for pdf_title and filename.
        """
        return {}

    def get_extra_context(self) -> dict:
        """
        Override to add extra context.
        """
        return {}


class BaseDocumentView(PermissionRequiredMixin, BasePDFDocumentView):
    """
    BasePDFDocumentView with specific methods for contest documents. Also handles permission checking for
    documents.generate_batch_document.
    """
    permission_required = 'documents.generate_batch_document'

    @cached_property
    def year(self) -> int:
        return int(self.kwargs['year'])

    def contestant_queryset(self) -> contest.models.Contestant.objects:
        return (contest.models.Contestant.objects
                .select_related('user', 'edition', 'assignation_semifinal_event',
                                'assignation_semifinal_event__center')
                .filter(edition__year=self.year)
                .order_by(*USER_LIST_ORDERING))

    @cached_property
    def contestants(self) -> contest.models.Contestant.objects:
        contestants = self.contestant_queryset()
        contestant_pk = self.kwargs.get('contestant')
        if contestant_pk:
            contestants = contestants.filter(pk=contestant_pk)  # returns zero or one result
            # assert we actually got the wanted contestant
            if not contestants.exists():
                raise Http404()
        return contestants

    @cached_property
    def events(self) -> contest.models.Event.objects:
        return (contest.models.Event.objects
                .select_related('edition', 'center')
                .filter(edition__year=self.year))

    def get_extra_context(self):
        context = super().get_extra_context()
        context['year'] = self.year
        context['events'] = self.events
        context['contestants'] = self.contestants
        context['site_url'] = settings.SITE_BASE_URL
        return context

    def i18nargs(self):
        args = {'year': self.year}
        contestant_pk = self.kwargs.get('contestant')
        if contestant_pk:
            args['username'] = self.contestants[0].user.username
            args['fullname'] = self.contestants[0].user.get_full_name()
        return args


class BaseSemifinalsDocumentView(BaseDocumentView):
    """
    BaseDocumentView with semifinal specifics.
    """
    def contestant_queryset(self):
        contestants = (super().contestant_queryset()
                       .filter(assignation_semifinal=contest.models.Assignation.assigned.value)
                       .exclude(assignation_semifinal_event=None))
        event_pk = self.kwargs.get('event')
        if event_pk and event_pk != 'all':
            contestants = contestants.filter(assignation_semifinal_event=self.event)
        return contestants

    def i18nargs(self):
        args = super().i18nargs()
        args['center'] = self.center_name
        return args

    @cached_property
    def events(self):
        return contest.models.Event.semifinals_for_edition(self.year)

    @cached_property
    def event(self) -> contest.models.Event:
        event_pk = self.kwargs.get('event')
        if event_pk and event_pk != 'all':
            return get_object_or_404(contest.models.Event, pk=event_pk)

    @cached_property
    def center_name(self) -> str:
        event_pk = self.kwargs.get('event')
        if event_pk == 'all':
            return _("all-centers")
        if event_pk:
            return self.event.center.name

    @cached_property
    def grouped_event_contestants(self):
        # FIXME: itertools.groupby won't work on Event instances, go figure why
        event_contestants = collections.defaultdict(list)
        for contestant in self.contestants.order_by('assignation_semifinal_event__date_begin', *USER_LIST_ORDERING):
            event_contestants[contestant.assignation_semifinal_event].append(contestant)
        return sorted(event_contestants.items(), key=lambda pair: pair[0].date_begin)


class BaseFinalDocumentView(BaseDocumentView):
    """
    BaseDocumentView with final specifics.
    """
    def contestant_queryset(self):
        return (super().contestant_queryset()
                .filter(assignation_final=contest.models.Assignation.assigned.value))

    @cached_property
    def events(self):
        return [self.final_event]

    @cached_property
    def final_event(self):
        event = contest.models.Event.final_for_edition(self.year)
        if not event.center:
            raise Http404("Final center does not exist.")
        return event

    def get_extra_context(self):
        context = super().get_extra_context()
        context['event'] = self.final_event
        return context

    @cached_property
    def grouped_event_contestants(self):
        return [(self.final_event, self.contestants)]


class BaseCompilationView(BaseDocumentView):
    """
    A special BaseDocumentView that takes any number of BaseDocumentView classes and runs pdfjoin on their
    respective output, in declaration order.

    The default permission is documents.generate_contestant_document so users may download their own documents.
    """
    compiled_classes = ()
    permission_required = 'documents.generate_contestant_document'

    def get_permission_object(self):
        return self.contestants.first()

    def render_to_response(self, context, **response_kwargs):
        import contextlib
        import subprocess

        def get_documents():
            for cls in self.compiled_classes:
                assert issubclass(cls, BaseDocumentView)
                # Hack: instantiate the view manually so we can access the required methods.
                # May break in future Django versions.
                view = cls()
                view.request = self.request
                view.args = self.args
                view.kwargs = self.kwargs
                template_name = view.get_template_names()[0]
                view_context = view.get_context_data()
                yield documents.models.generate_tex_pdf(template_name, view_context)

        # generate_tex_pdf is a context manager that cleans up the temporary files once exited, thus we need to use a
        # stack of context managers to keep them open while we pdfjoin the output files.
        # Once the stack exited, the context managers will be released and output files cleaned up.
        with contextlib.ExitStack() as stack:
            filenames = []
            for document in get_documents():
                try:
                    filenames.append(stack.enter_context(document))
                except prologin.utils.SubprocessFailedException as err:
                    error = err
                    # abort early
                    break
            else:
                # there was no error
                process = subprocess.Popen(['pdfjoin',
                                            '--vanilla',  # don't read disk conf files
                                            '--tidy',  # delete temporary output
                                            # this is where we have a chance to set the PDF author/title
                                            '--pdfauthor', "Prologin",
                                            '--pdftitle', self.get_pdf_title(),
                                            '--outfile', '/dev/stdout'] + filenames,
                                           stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                try:
                    stdout, stderr = process.communicate()
                    if process.returncode != 0 or not stdout:
                        error = prologin.utils.SubprocessFailedException("pdfjoin failed",
                                                                         process.returncode, stdout, stderr)
                    else:
                        response = HttpResponse(content=stdout, content_type=self.content_type)
                        self.apply_headers(response)
                        return response
                except subprocess.CalledProcessError as err:
                    process.kill()
                    stdout, stderr = process.communicate()
                    error = prologin.utils.SubprocessFailedException("pdfjoin failed", err.returncode, stdout, stderr)

        # Code reached if something went wrong
        if self.can_display_tex_errors():
            return self.response_class(self.request,
                                       template='documents/tex-error-debug.html',
                                       context={'error': error},
                                       status=500)
        return HttpResponseServerError()
