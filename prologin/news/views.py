from django.core.urlresolvers import reverse
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin

from zinnia.models import Entry
from zinnia.url_shortener.backends.default import base36


class LegacyUrlRedirectView(SingleObjectMixin, RedirectView):
    model = Entry
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse('zinnia:entry_shortlink', args=[base36(self.get_object().pk)])
