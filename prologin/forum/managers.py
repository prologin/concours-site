from django.db import models
from django.db.models import Case, When, F, Q, Value, Min, Max


class ThreadObjectManager(models.Manager):
    def with_readstate_of(self, user=None):
        '''Adds a seen field to threads'''
        return (self.get_queryset()
                # Get the id of the first and last post in the thread
                .annotate(first_post_id=Min('posts__id'))
                .annotate(last_post_id=Max('posts__id'))
                # Get the id of the last post seen by the user
                .annotate(last_read_post_id=Max(
                    'read_states__post__id',
                    filter=Q(read_states__user=user)))
                # seen=True only if the last post has been seen by the user
                .annotate(seen=Case(
                    When(last_post_id=F('last_read_post_id'),
                         then=Value(True)),
                    default=Value(False),
                    output_field=models.BooleanField())))


class VisibleObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_visible=True)
