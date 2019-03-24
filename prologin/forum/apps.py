from django.apps import AppConfig

class ForumConfig(AppConfig):
    name = 'forum'
    verbose_name = 'Forum'

    def ready(self):
        import forum.signals
