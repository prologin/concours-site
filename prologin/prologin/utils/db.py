from django.db.models import Case, When, Value


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
        cases = (When(**{field: key, 'then': Value(value)})
                 for key, value in mapping)
        super().__init__(*cases, **kwargs)
