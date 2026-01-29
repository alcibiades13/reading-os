"""
Management command to clean up duplicate books in the database.

When books are imported without ISBN (e.g., from Goodreads), they can be
created multiple times because there's no unique identifier to check.

This command:
1. Finds all books with duplicate titles
2. For each group of duplicates, keeps the one with the most data (UserBooks, Quotes)
3. Transfers any data from duplicates to the keeper
4. Deletes the empty duplicates

Usage:
    python manage.py cleanup_duplicates --dry-run  # Preview what will be deleted
    python manage.py cleanup_duplicates            # Actually delete duplicates
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.signals import post_delete
from apps.books.models import Book
from apps.reading.models import UserBook, Quote
from apps.reading import models as reading_models


class Command(BaseCommand):
    help = 'Clean up duplicate books in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each duplicate',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE ===\n'))

        # Find all titles with duplicates
        duplicates = (
            Book.objects
            .values('title')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        total_titles = duplicates.count()
        total_deleted = 0
        total_userbooks_transferred = 0
        total_quotes_transferred = 0

        self.stdout.write(f'Found {total_titles} titles with duplicates\n')

        for dup in duplicates:
            title = dup['title']
            count = dup['count']

            # Get all books with this title, ordered by amount of data
            books = list(
                Book.objects
                .filter(title=title)
                .annotate(
                    userbook_count=Count('user_books'),
                    quote_count=Count('quotes'),
                    data_score=Count('user_books') + Count('quotes')
                )
                .order_by('-data_score', 'created_at')  # Most data first, then oldest
            )

            if len(books) < 2:
                continue

            # The keeper is the one with most data (or oldest if tied)
            keeper = books[0]
            to_delete = books[1:]

            if verbose:
                self.stdout.write(f'\n--- {title[:50]} ({count}x) ---')
                self.stdout.write(f'  Keeping: ID {keeper.id} (UserBooks: {keeper.userbook_count}, Quotes: {keeper.quote_count})')

            for book in to_delete:
                userbook_count = book.user_books.count()
                quote_count = book.quotes.count()

                if verbose:
                    self.stdout.write(f'  Deleting: ID {book.id} (UserBooks: {userbook_count}, Quotes: {quote_count})')

                if not dry_run:
                    with transaction.atomic():
                        # Disconnect problematic signals during cleanup
                        post_delete.disconnect(
                            reading_models.update_quotes_count_on_delete,
                            sender=Quote
                        )

                        try:
                            # Transfer UserBooks to keeper
                            if userbook_count > 0:
                                for ub in book.user_books.all():
                                    # Check if user already has keeper book
                                    existing = UserBook.objects.filter(
                                        user=ub.user,
                                        book=keeper
                                    ).first()

                                    if existing:
                                        # Merge: keep the one with more data
                                        if ub.rating and not existing.rating:
                                            existing.rating = ub.rating
                                        if ub.review and not existing.review:
                                            existing.review = ub.review
                                        if ub.started_at and not existing.started_at:
                                            existing.started_at = ub.started_at
                                        if ub.finished_at and not existing.finished_at:
                                            existing.finished_at = ub.finished_at
                                        existing.save()

                                        # Transfer quotes from ub to existing before deleting
                                        Quote.objects.filter(user_book=ub).update(user_book=existing)
                                        ub.delete()
                                    else:
                                        # Transfer to keeper
                                        ub.book = keeper
                                        ub.save()
                                    total_userbooks_transferred += 1

                            # Transfer Quotes to keeper
                            if quote_count > 0:
                                for quote in book.quotes.all():
                                    quote.book = keeper
                                    quote.book_title = keeper.title
                                    quote.save()
                                    total_quotes_transferred += 1

                            # Delete the duplicate book
                            book.delete()
                        finally:
                            # Reconnect signals
                            post_delete.connect(
                                reading_models.update_quotes_count_on_delete,
                                sender=Quote
                            )

                total_deleted += 1

        # Summary
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Would delete {total_deleted} duplicate books'))
            self.stdout.write(self.style.WARNING(f'Would transfer {total_userbooks_transferred} UserBooks'))
            self.stdout.write(self.style.WARNING(f'Would transfer {total_quotes_transferred} Quotes'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Deleted {total_deleted} duplicate books'))
            self.stdout.write(self.style.SUCCESS(f'Transferred {total_userbooks_transferred} UserBooks'))
            self.stdout.write(self.style.SUCCESS(f'Transferred {total_quotes_transferred} Quotes'))
