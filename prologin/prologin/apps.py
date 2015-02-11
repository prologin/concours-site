from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class ProloginConfig(AppConfig):
    name = 'prologin'
    verbose_name = "Prologin"

    def ready(self):
        Edition = self.get_model('contest.Edition')
        try:
            Edition.latest = Edition.objects.filter(active=True).order_by('-year')[0]
        except IndexError:
            raise ImproperlyConfigured("You must define at least one active contest.Edition")
