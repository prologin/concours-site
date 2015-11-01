from django.db import models
from django.utils.translation import ugettext_noop, ugettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from prologin.utils import ChoiceEnum
from prologin.languages import Language


@ChoiceEnum.labels(str.capitalize)
class Gender(ChoiceEnum):
    male = 0
    female = 1
    ugettext_noop("Male")
    ugettext_noop("Female")


class BaseEnumField:
    def __init__(self, enum, *args, **kwargs):
        assert issubclass(enum, ChoiceEnum)
        kwargs['choices'] = enum.choices(empty_label=kwargs.pop('empty_label', None))
        self._enum = enum
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, [self._enum] + args, kwargs


class EnumField(BaseEnumField, models.PositiveSmallIntegerField):
    pass


class TextEnumField(BaseEnumField, models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 64
        super().__init__(*args, **kwargs)


def _enumfield_factory(basecls, enumcls, name, **fieldkwargs):
    def init(self, *args, **kwargs):
        defaults = dict(fieldkwargs)
        defaults.update(kwargs)
        basecls.__init__(self, enumcls, *args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = basecls.deconstruct(self)
        return name, path, args[1:], kwargs

    return type(name, (basecls,), {'__init__': init, 'deconstruct': deconstruct})


GenderField = _enumfield_factory(EnumField, Gender, 'GenderField',
                                 empty_label=_("Other or prefer not to tell"), verbose_name=_("Gender"))

CodingLanguageField = _enumfield_factory(TextEnumField, Language, 'CodingLanguageField',
                                         verbose_name=_("Coding language"))


class AddressableModel(models.Model):
    address = models.TextField(blank=True, verbose_name=_("Address"))
    postal_code = models.CharField(max_length=32, blank=True, verbose_name=_("Postal code"))
    city = models.CharField(max_length=64, blank=True, verbose_name=_("City"))
    country = models.CharField(max_length=64, blank=True, verbose_name=_("Country"))

    class Meta:
        abstract = True


class ContactModel(models.Model):
    contact_gender = GenderField(null=True, blank=True)
    contact_position = models.CharField(max_length=128, blank=True)
    contact_first_name = models.CharField(max_length=64, blank=True)
    contact_last_name = models.CharField(max_length=64, blank=True)
    contact_phone_desk = models.CharField(max_length=16, blank=True)
    contact_phone_mobile = models.CharField(max_length=16, blank=True)
    contact_phone_fax = models.CharField(max_length=16, blank=True)
    contact_email = models.EmailField(blank=True)

    def get_full_name(self):
        return " ".join(field for field in
                        (self.contact_first_name, self.contact_last_name) if field)

    class Meta:
        abstract = True


