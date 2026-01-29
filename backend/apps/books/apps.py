from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.books"

    def ready(self):
        """Register custom lookups when app is ready."""
        from django.contrib.postgres.lookups import Unaccent
        from django.db.models import CharField, TextField

        # Register unaccent lookup for accent-insensitive search
        # This allows queries like: Book.objects.filter(title__unaccent__icontains='c')
        # to match titles with 'č', 'ć', etc.
        CharField.register_lookup(Unaccent)
        TextField.register_lookup(Unaccent)
