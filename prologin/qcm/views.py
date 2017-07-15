from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView
from django.views.generic.edit import ModelFormMixin
import rules
import random
from rules.contrib.views import PermissionRequiredMixin

import qcm.forms
import qcm.models
import qcm.rules


class DisplayQCMView(PermissionRequiredMixin, UpdateView):
    template_name = "qcm/display.html"
    slug_url_kwarg = 'year'
    pk_url_kwarg = 'year'
    context_object_name = 'qcm'
    form_class = qcm.forms.QcmForm
    queryset = qcm.models.Qcm.full_objects.all()
    permission_required = 'qcm.view_qcm'

    @cached_property
    def event(self):
        return self.object.event

    @property
    def year(self):
        return self.kwargs[self.pk_url_kwarg]

    @property
    def can_view_correction(self):
        return self.request.user.has_perm('qcm.view_correction', self.object)

    @property
    def can_save_answers(self):
        return self.request.user.has_perm('qcm.save_answers', self.object)

    def get_success_url(self):
        return reverse('qcm:display', args=[self.year])

    def get_object(self, queryset=None):
        try:
            return ((self.get_queryset() if queryset is None else queryset)
                    .get(event__edition__year=self.year))
        except self.model.DoesNotExist:
            raise Http404()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.can_view_correction:
            # just display the form so we can show right/wrong answers
            return self.form_invalid(self.get_form())
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.can_save_answers:
            # bypasses form.save(), just redirects
            return super(ModelFormMixin, self).form_valid(form)
        messages.success(self.request, _("Your new answers have been saved."))
        # calls form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contestant'] = self.request.current_contestant
        if self.request.user.is_authenticated():
            ordering_seed = self.request.user.pk
        else:
            try:
                ordering_seed = self.request.session['ordering_seed']
            except KeyError:
                ordering_seed = self.request.session['ordering_seed'] = random.random()
        kwargs['ordering_seed'] = ordering_seed
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qcm_can_receive_answers'] = rules.Predicate(qcm.rules.can_save_answers).test(None, self.object)
        context['user_can_save_answers'] = self.can_save_answers
        context['user_can_view_correction'] = self.can_view_correction
        context['correction_mode'] = self.request.method == 'POST'
        return context
