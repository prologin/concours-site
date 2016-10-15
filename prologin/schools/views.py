from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin

import schools.models


class FacebookPictureView(LoginRequiredMixin, SingleObjectMixin, RedirectView):
    model = schools.models.School
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        school = self.get_object()
        url = school.picture
        if url:
            return url
        raise Http404()


class SchoolSearchView(LoginRequiredMixin, ListView):
    model = schools.models.School
    paginate_by = 5
    max_facebook_results = 3

    @cached_property
    def query(self):
        return self.request.GET.get('q', '')

    def get_queryset(self):
        q = Q()
        current_school = self.request.current_contestant.school
        if current_school:
            q |= Q(name__icontains=self.query, pk=current_school.pk)
        q |= Q(approved=True) & (Q(name__iexact=self.query) | Q(acronym__iexact=self.query))
        q |= Q(approved=True) & (Q(name__icontains=self.query) | Q(acronym__icontains=self.query))
        token_q = Q(approved=True)
        for token in (token for token in map(str.strip, self.query.split()) if token):
            token_q &= (Q(name__icontains=token) | Q(acronym__icontains=token))
        q |= token_q
        return super().get_queryset().filter(q)

    def render_to_response(self, context, **response_kwargs):
        paginator = context['paginator']
        # Database results
        results = [{'id': school.pk,
                    'text': ' – '.join([school.name] + ([school.city] if school.city else [])),
                    'official': school.approved,
                    'picture': reverse('schools:fb-picture', args=[school.pk])}
                   for school in context['object_list']]
        known_names = {item['text'].lower() for item in results}
        # Facebook results
        fb_results = []
        for result in schools.models.Facebook.search(self.query):
            if result['name'].lower() in known_names:
                continue
            try:
                picture = result['picture']['data']['url']
            except KeyError:
                picture = None
            fb_results.append({'id': '_new_fb_{}'.format(result['id']),
                               'text': result['name'],
                               'official': False,
                               'picture': picture})
            if len(fb_results) == self.max_facebook_results:
                break
        results += fb_results
        return JsonResponse({
            'items': results,
            'total': paginator.count + len(fb_results),
        })
