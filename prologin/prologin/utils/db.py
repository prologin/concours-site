from django.db import models
from django.db.models import Case, When, Value, Sum, IntegerField
from django.utils.translation import ugettext_lazy as _

from prologin.utils import msgpack_loads, msgpack_dumps


class CaseMapping(Case):
    """
    Wrapper around the Case annotation that provides a mapping between a field
    and an associated value.

    class Foo(models.Model):
        field = models.CharField(choices=['a', 'b', 'c'])

    Foo.objects
       .annotate(order=CaseMapping('field', [('a', 23), ('b', 11), ('c', 0)]))
       .order_by('-order')
    """
    def __init__(self, field, mapping, **kwargs):
        cases = [When(**{field: key, 'then': Value(value)}) for key, value in mapping]
        super().__init__(*cases, **kwargs)


class ConditionalSum(Sum):
    """
    Wrapper around the Sum annotation that provides a conditional sum.

    class Foo(models.Model):
        pass

    class Bar(models.Model):
        foo = models.ForeignKey(Bar, related_name='bars', on_delete=models.CASCADE)
        ok = models.BooleanField()

    Foo.objects.annotate(
        ok_count=ConditionalSum(bars__state=True),
        nok_count=ConditionalSum(bars__state=False))
    """
    def __init__(self, **mapping):
        super(ConditionalSum, self).__init__(*[
            Case(When(**{field: value, 'then': Value(1)}), default=0, output_field=IntegerField())
            for field, value in mapping.items()
        ])


class AdminOrderFieldsMixin:
    """
    Mixin to automatically annotate() a ModelAdmin queryset with sortable
    (computed) fields and add the corresponding getters, so it is possible
    to sort on these fields.

    Sample usage:

    class FooAdmin(AdminOrderFieldsMixin, ModelAdmin):
        list_display = ['some_name']
        annotations = [
            # a name              # an annotate()-compatible expr
            ('related_obj_count', Count('related_objs')),
            # or
            ('related_obj_count', Count('related_objs'), "Human description"),
        ]
    """
    annotations = []

    def __init__(self, *args, **kwargs):
        # monkey-patch the instance with the annotations
        for annotation in self.get_annotations():
            try:
                name, func = annotation
                text = _(name.replace('_', ''))
            except ValueError:
                name, func, text = annotation

            def method(obj):
                return getattr(obj, name)
            method.__qualname__ = name
            method.admin_order_field = name
            method.short_description = text

            setattr(self, name, method)

        super().__init__(*args, **kwargs)

    def get_annotations(self):
        return self.annotations

    def get_queryset(self, request):
        kwargs = {}
        for annotation in self.get_annotations():
            try:
                name, func = annotation
            except ValueError:
                name, func, text = annotation
            if callable(func):
                func = func(request)
            kwargs[name] = func

        return super().get_queryset(request).annotate(**kwargs)


class MsgpackField(models.Field):
    description = "Msgpack encoded data"
    empty_values = [None, b'']

    def __init__(self, *args, **kwargs):
        kwargs['editable'] = False
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['editable']
        return name, path, args, kwargs

    def get_internal_type(self):
        return "BinaryField"

    def get_placeholder(self, value, compiler, connection):
        return connection.ops.binary_placeholder_sql(value)

    def get_default(self):
        if self.has_default() and not callable(self.default):
            return self.default
        default = super().get_default()
        if default == '':
            return None
        return default

    def get_db_prep_value(self, value, connection=None, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        if value is not None:
            return connection.Database.Binary(value)
        return value

    def value_to_string(self, obj):
        return self.value_from_object(obj)

    def get_prep_value(self, value):
        if value is None:
            return None
        return msgpack_dumps(value)

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return msgpack_loads(value)
