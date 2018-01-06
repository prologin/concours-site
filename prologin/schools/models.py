import hashlib
import logging

import requests
from django.conf import settings
from django.db import models
from django.core.cache import cache
from django.db.models import Sum, Count, Value, Case, When, IntegerField
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from prologin.models import AddressableModel
from prologin.utils import upload_path


class ApprovedSchoolManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(approved=True)


class School(AddressableModel):
    def picture_upload_to(self, *args, **kwargs):
        return upload_path('school', using=lambda p: p.pk)(self, *args, **kwargs)

    name = models.CharField(max_length=512, blank=False, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)

    # Optional fields
    imported = models.BooleanField(default=False, blank=True)
    uai = models.CharField(max_length=16, blank=True, null=True, db_index=True,
                           unique=True)
    acronym = models.CharField(max_length=32, blank=True)
    type = models.CharField(max_length=128, blank=True)
    academy = models.CharField(max_length=128, blank=True)
    lat = models.DecimalField(default=0, max_digits=16, decimal_places=6,
                              null=True, blank=True)
    lng = models.DecimalField(default=0, max_digits=16, decimal_places=6,
                              null=True, blank=True)

    objects = models.Manager()
    approved_schools = ApprovedSchoolManager()

    def edition_contestants(self, year):
        return self.contestants.filter(edition__year=year)

    @property
    def current_edition_contestants(self):
        return self.edition_contestants(settings.PROLOGIN_EDITION)

    @property
    def total_contestants_count(self):
        return self.contestants.count()

    @property
    def current_edition_contestants_count(self):
        return self.current_edition_contestants.count()

    @property
    def picture(self):
        for field in (self.name, self.acronym):
            if field:
                try:
                    return Facebook.search(field)[0]['picture']['data']['url']
                except (IndexError, KeyError):
                    continue

    def clean(self):
        if self.uai == '':
            self.uai = None

    def __str__(self):
        name = self.name + (" ({})".format(self.acronym) if self.acronym else "")
        return "{}, {}".format(name, self.city)

    class Meta:
        ordering = ('approved', 'name')
        verbose_name = _("school")
        verbose_name_plural = _("schools")

    func_total_contestants_count = Count('contestants')
    func_current_edition_contestants_count = lambda edition: \
        Sum(Case(When(contestants__edition__year=edition, then=Value(1)), default=Value(0),
                 output_field=IntegerField()))


class Facebook:
    params = {'access_token': settings.FACEBOOK_GRAPH_API_ACCESS_TOKEN,
              'fields': 'id,about,bio,category,description,general_info,link,name,website,picture',
              'format': 'json', 'pretty': '0'}

    @classmethod
    def _params(cls, **kwargs):
        p = cls.params.copy()
        p.update(kwargs)
        return p

    @classmethod
    def _request(cls, method, **kwargs):
        return requests.get('https://graph.facebook.com/v2.7' + method, params=cls._params(**kwargs), timeout=2).json()

    @classmethod
    def search(cls, query):
        query = query.strip().lower()
        if not query:
            return []

        def get_data():
            try:
                return [item for item in cls._request('/search', q=query, type='place')['data']
                        if item.get('category') in ('School', 'University')]
            except Exception:
                return []

        key = hashlib.sha1(query.encode('utf8', 'replace')).hexdigest()
        return cache.get_or_set('schools/search/' + key, get_data, 60 * 60 * 24)

    @classmethod
    def get(cls, id):
        def get_data():
            try:
                return cls._request('/' + id)
            except Exception:
                return None

        key = hashlib.sha1(id.encode('utf8', 'replace')).hexdigest()
        return cache.get_or_set('schools/id/' + key, get_data, 60 * 60 * 24)


@receiver(post_save, sender=School)
def notify_school_created(sender, instance, **kwargs):
    s = settings.PROLOGIN_NEW_SCHOOL_NOTIFY
    if not s:
        return
    if not kwargs.get('created') or instance.imported or instance.approved:
        return
    data = {'name': instance.name,
            'url': settings.SITE_BASE_URL + reverse('admin:schools_school_change', args=[instance.pk])}
    try:
        requests.request(s['method'], s['url'], json=data, **s.get('kwargs', {}))
    except Exception:
        logging.exception("Could not notify of new-school")
