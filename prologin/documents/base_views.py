from django.http.response import Http404, HttpResponse, HttpResponseServerError
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from rules.contrib.views import PermissionRequiredMixin

import contest.models
import documents.models


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

    def render_to_response(self, context, **response_kwargs):
        context['pdf_title'] = self.get_pdf_title()
        try:
            with documents.models.generate_tex_pdf(self.get_template_names()[0], context) as output:
                response = HttpResponse(content=open(output, 'rb'), content_type=self.content_type)
                self.apply_headers(response)
                return response
        except documents.models.SubprocessFailedException as error:
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

    def i18nargs(self):
        """
        Override to customize the context catalogue for pdf_title and filename.
        """
        return {}


class BaseContestDocumentView(PermissionRequiredMixin, BasePDFDocumentView):
    """
    Mixin that exposes useful data, including:
        - the edition year
        - the centers, from the path argument 'center'
        - the human-friendly center name
        - the list of contestants for the event
        - the single contestant if path has the 'contestant' argument
        - the list of events for an edition

    Also implements permission checking.
    """
    permission_required = 'documents.generate_batch_document'
    event_type = None

    @property
    def year(self) -> int:
        return int(self.kwargs['year'])

    @cached_property
    def centers(self) -> contest.models.Center.objects:
        center = self.kwargs.get('center')
        if center:
            return contest.models.Center.objects.filter(pk=center)

    @cached_property
    def center_name(self) -> str:
        if self.kwargs.get('center') == 'all':
            return _("all-centers")
        return self.centers.first().name

    @cached_property
    def contestants(self) -> contest.models.Contestant.objects:
        contestants = (contest.models.Contestant.objects
                       .select_related('user', 'edition', 'assignation_semifinal_event',
                                       'assignation_semifinal_event__center')
                       .filter(edition__year=self.year))
        if self.event_type is contest.models.Event.Type.semifinal:
            contestants = (contestants
                           .filter(assignation_semifinal=contest.models.Assignation.assigned.value)
                           .exclude(assignation_semifinal_event=None))
            center = self.kwargs.get('center')
            if center and center != 'all':
                contestants = contestants.filter(assignation_semifinal_event__center=center)
        elif self.event_type is contest.models.Event.Type.final:
            contestants = contestants.filter(assignation_final=contest.models.Assignation.assigned.value)
        return contestants

    @cached_property
    def contestant(self) -> contest.models.Contestant:
        contestant_pk = self.kwargs.get('contestant')
        if contestant_pk:
            try:
                return (contest.models.Contestant.objects
                        .select_related('user', 'edition', 'assignation_semifinal_event',
                                        'assignation_semifinal_event__center')
                        .get(pk=contestant_pk))
            except contest.models.Contestant.DoesNotExist:
                raise Http404()

    @cached_property
    def events(self) -> contest.models.Event.objects:
        return (contest.models.Event.objects
                .select_related('edition', 'center')
                .filter(edition__year=self.year, type=self.event_type.value))

    @cached_property
    def final_event(self) -> contest.models.Event:
        return contest.models.Event.final_for_edition(self.year)

    def i18nargs(self):
        args = {'year': self.year}
        if self.contestant:
            args['username'] = self.contestant.user.username
            args['fullname'] = self.contestant.user.get_full_name()
        if self.centers:
            args['center'] = self.center_name
        return args


class BaseContestCompilationView(BaseContestDocumentView):
    """
    A special BaseContestDocumentView that takes any number of BaseContestDocumentView classes and runs pdfjoin on their
    respective output, in declaration order.

    The default permission is documents.generate_contestant_document so users may download their own documents.
    """
    compiled_classes = ()
    permission_required = 'documents.generate_contestant_document'

    def get_permission_object(self):
        return self.contestant

    def render_to_response(self, context, **response_kwargs):
        import contextlib
        import subprocess

        def get_documents():
            for cls in self.compiled_classes:
                assert issubclass(cls, BaseContestDocumentView)
                # Hack: instantiate the view manually so we can access the required methods.
                # May break in future Django versions.
                view = cls()
                view.request = self.request
                view.args = self.args
                view.kwargs = self.kwargs
                template_name = view.get_template_names()[0]
                context = view.get_context_data()
                yield documents.models.generate_tex_pdf(template_name, context)

        # generate_tex_pdf is a context manager that cleans up the temporary files once exited, thus we need to use a
        # stack of context managers to keep them open while we pdfjoin the output files.
        # Once the stack exited, the context managers will be released and output files cleaned up.
        with contextlib.ExitStack() as stack:
            filenames = []
            for document in get_documents():
                try:
                    filenames.append(stack.enter_context(document))
                except documents.models.SubprocessFailedException as err:
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
                        error = documents.models.SubprocessFailedException("pdfjoin failed", process.returncode, stdout, stderr)
                    else:
                        response = HttpResponse(content=stdout, content_type=self.content_type)
                        self.apply_headers(response)
                        return response
                except subprocess.CalledProcessError as err:
                    process.kill()
                    stdout, stderr = process.communicate()
                    error = documents.models.SubprocessFailedException("pdfjoin failed", err.returncode, stdout, stderr)

        # Code reached if something went wrong
        if self.can_display_tex_errors():
            return self.response_class(self.request,
                                       template='documents/tex-error-debug.html',
                                       context={'error': error},
                                       status=500)
        return HttpResponseServerError()
