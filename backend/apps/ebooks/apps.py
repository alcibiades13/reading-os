from django.apps import AppConfig


class EbooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ebooks"

    def ready(self):
        from apps.ebooks import signals  # noqa: F401
