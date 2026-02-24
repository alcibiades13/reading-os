from django.apps import AppConfig


class ContributionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contributions'

    def ready(self):
        import apps.contributions.signals  # noqa
