from django.db import models


class VisibleObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_visible=True)
