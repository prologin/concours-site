from collections import namedtuple
from django.db import models
from django.db.models import BooleanField, CharField, IntegerField
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from prologin.models import TextEnumField
from prologin.utils import ChoiceEnum
from prologin.models import AddressableModel, ContactModel
from prologin.utils import upload_path
from prologin.utils.db import CaseMapping


class RankData(
        namedtuple('Rank', 'name significance public')):
    def __lt__(self, other):
        return self.significance.__lt__(other.significance)


class Rank(ChoiceEnum):
    gold = RankData("Gold", 90, True)
    silver = RankData("Silver", 60, True)
    copper = RankData("Bronze", 30, True)

    @classmethod
    def label_for(cls, member):
        return member.value.name

    @classmethod
    def _get_choices(cls):
        return tuple((m.name, cls.label_for(m)) for m in cls)


class ActiveSponsorManager(models.Manager):
    def get_queryset(self):
        rank_significance = CaseMapping('rank_code',
                                ((rank.name, rank.value.significance)
                                    for rank in Rank),
                                output_field=IntegerField())
        rank_public = CaseMapping('rank_code',
                                  ((rank.name, rank.value.public)
                                   for rank in Rank),
                                  output_field=BooleanField())
        return (super().get_queryset().filter(is_active=True)
                .annotate(rank_significance=rank_significance,
                            rank_public=rank_public))
                #.order_by('-rank_significance'))


class Sponsor(AddressableModel, ContactModel, models.Model):
    def upload_logo_to(self, *args, **kwargs):
        return upload_path('sponsor')(self, *args, **kwargs)

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_logo_to, blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    rank_code = TextEnumField(Rank, verbose_name=_("Rank"),
                                    db_index=True,
                                    blank=False,
                                    null=False)
    objects = models.Manager()
    active = ActiveSponsorManager()

    @property
    def rank(self):
        return Rank[self.rank_code]

    @property
    def rank_name(self):
        return getattr(self.rank.value, 'name')

    def __str__(self):
        return self.name
