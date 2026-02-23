from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.books"

    def ready(self):
        """Register custom lookups and signals when app is ready."""
        from django.contrib.postgres.lookups import Unaccent
        from django.db.models import CharField, TextField

        # Register unaccent lookup for accent-insensitive search
        CharField.register_lookup(Unaccent)
        TextField.register_lookup(Unaccent)

        import apps.books.signals  # noqa: F401
