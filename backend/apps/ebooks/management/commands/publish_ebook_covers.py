from django.core.management.base import BaseCommand

from apps.ebooks.models import EBook
from apps.ebooks.progress import publish_cover_to_book


class Command(BaseCommand):
    help = "Copy e-book covers to linked catalog books that have no cover (shows them in the library)."

    def handle(self, *args, **options):
        updated = 0
        for ebook in EBook.objects.filter(book__isnull=False).exclude(cover='').select_related('book'):
            if publish_cover_to_book(ebook):
                updated += 1
                self.stdout.write(f'  {ebook.book.title}')
        self.stdout.write(self.style.SUCCESS(f'Covers added to {updated} book(s).'))
