from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ContestConfig(AppConfig):
    name = 'contest'
    verbose_name = 'Contest'

    def ready(self):
        Event = self.get_model('Event')
        try:
            Event.objects.select_related('edition').filter(edition__year=settings.PROLOGIN_EDITION)[0]
        except IndexError:
            raise ImproperlyConfigured("You need to configure at least one Edition "
                                       "and one related Event for this year ({})".format(settings.PROLOGIN_EDITION))