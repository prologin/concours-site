from django import forms
from django.contrib.admin import ModelAdmin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.utils.text import ugettext_lazy as _
from django.views.generic.edit import UpdateView
from django.apps import apps
from rules.contrib.views import PermissionRequiredMixin

from contest.models import Contestant
from schools.models import School

from django.contrib.admin import site


class MergeSchoolForm(forms.ModelForm):
    add_to_merge = forms.ModelChoiceField(School.objects.all(), required=False, label=_("Add to merge"),
                                          widget=ForeignKeyRawIdWidget(Contestant._meta.get_field('school').rel, site))

    class Meta:
        model = School
        fields = ('name', 'uai', 'acronym', 'type', 'academy',
                  'address', 'postal_code', 'city', 'country',
                  'lat', 'lng', 'approved', 'imported')

    # hack to include the JS for ForeignKeyRawIdWidget
    media = ModelAdmin(School, site).media


class MergeView(PermissionRequiredMixin, UpdateView):
    template_name = 'admin/schools/merge.html'
    pk_url_kwarg = 'pks'
    model = School
    form_class = MergeSchoolForm
    context_object_name = 'school'
    success_url = reverse_lazy('admin:schools_school_changelist')
    permission_required = 'schools.merge'

    def get(self, request, *args, **kwargs):
        remove = request.GET.get('remove')
        if remove:
            schools = set(self.kwargs[self.pk_url_kwarg].split(','))
            schools.discard(remove)
            return redirect(reverse_lazy('schools:admin:merge', args=[','.join(schools)]))
        return super(MergeView, self).get(request, *args, **kwargs)

    @cached_property
    def schools(self):
        pks = self.kwargs[self.pk_url_kwarg].split(',')
        return self.get_queryset().filter(pk__in=pks).order_by('pk')

    @cached_property
    def schools_to_merge(self):
        # schools that will be deleted, replaced by the merged school
        return self.schools.exclude(pk=self.get_object().pk)

    @cached_property
    def contestants_to_merge(self):
        # contestants whose school will be replaced by the merged school
        return School.contestants.field.model.objects.filter(school__in=self.schools_to_merge)

    def get_queryset(self):
        return (super().get_queryset()
                .annotate(contestant_count=Count('contestants')))

    def get_object(self, queryset=None):
        use = self.request.GET.get('use')
        try:
            return self.schools.get(pk=use)
        except School.DoesNotExist:
            return self.schools.first()

    def form_valid(self, form):
        # school that will be kept (and updated if user did so)
        base_school = self.get_object()
        with transaction.atomic():
            self.contestants_to_merge.update(school=base_school)
            self.schools_to_merge.delete()
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(MergeView, self).get_context_data(**kwargs)
        app_label = 'schools'
        context.update({
            'app_label': app_label,
            'app_config': apps.get_app_config(app_label),
            'schools': self.schools,
            'deleted_school_count': self.schools_to_merge.count(),
            'updated_contestant_count': self.contestants_to_merge.count(),
        })
        return context
