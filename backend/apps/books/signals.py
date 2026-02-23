import threading
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='books.Author')
def auto_enrich_new_author(sender, instance, created, **kwargs):
    """
    When a new Author is created, attempt to enrich it with bio/photo/dates
    in a background thread so it doesn't block the request.
    """
    if not created:
        return

    # Skip if author already has data (e.g. created via admin with manual data)
    if instance.bio and instance.photo and instance.birth_date:
        return

    def _enrich():
        try:
            from apps.books.author_enrichment import enrich_author
            updated = enrich_author(instance)
            if updated:
                logger.info(
                    f'Auto-enriched new author "{instance.name}": {list(updated.keys())}'
                )
        except Exception as e:
            logger.warning(f'Auto-enrichment failed for "{instance.name}": {e}')

    thread = threading.Thread(target=_enrich, daemon=True)
    thread.start()
