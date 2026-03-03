"""
Management command to clean up duplicate books in the database.

When books are imported multiple times, they can be created as exact copies.

This command:
1. Groups books by title + same authors
2. Within each group, sub-groups by content signature (description, pages, isbn, cover, source)
3. Only deletes books that are TRULY identical (same content signature)
4. Different editions (different pages, isbn, cover, source) are NEVER deleted
5. Transfers all related data from duplicates to the keeper

Usage:
    python manage.py cleanup_duplicates --dry-run         # Preview
    python manage.py cleanup_duplicates --dry-run --verbose
    python manage.py cleanup_duplicates                   # Execute
"""

import sys
import io
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_delete
from apps.books.models import Book, BookDNAVote
from apps.reading.models import UserBook, Quote, VocabularyWord
from apps.reading.models_study import StudyNote
from apps.reading import models as reading_models

try:
    from apps.lists.models import ReadingListItem
except ImportError:
    ReadingListItem = None

try:
    from apps.codex.models import JournalEntry
except ImportError:
    JournalEntry = None


def content_signature(book):
    """
    Generate a signature from the book's actual content fields.
    Books with different signatures are different editions and must NOT be merged.
    """
    return (
        (book.description or '')[:100],
        book.pages,
        book.isbn or '',
        (book.cover_image or '')[:50],
        book.source or '',
        book.publisher_id,
    )


class Command(BaseCommand):
    help = 'Clean up duplicate books (only truly identical copies, never different editions)'

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
        # Fix encoding for Windows console
        if sys.platform == 'win32':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            self.stdout._out = sys.stdout

        dry_run = options['dry_run']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE ===\n'))

        # Group books by title + sorted author IDs
        title_groups = defaultdict(list)
        all_books = Book.objects.prefetch_related('authors').all()

        for book in all_books:
            author_ids = tuple(sorted(book.authors.values_list('id', flat=True)))
            key = (book.title.strip().lower(), author_ids)
            title_groups[key].append(book)

        # Filter to only groups with duplicates
        duplicate_groups = {k: v for k, v in title_groups.items() if len(v) > 1}

        total_groups = len(duplicate_groups)
        total_deleted = 0
        skipped_different = 0
        stats = {
            'userbooks': 0,
            'quotes': 0,
            'study_notes': 0,
            'vocabulary': 0,
            'list_items': 0,
            'journal': 0,
            'dna_votes': 0,
            'book_groups': 0,
        }

        self.stdout.write(f'Found {total_groups} title+author groups with multiple books\n')

        for (title, author_ids), books in sorted(duplicate_groups.items(), key=lambda x: -len(x[1])):
            # Sub-group by content signature to find truly identical books
            sig_groups = defaultdict(list)
            for book in books:
                sig = content_signature(book)
                sig_groups[sig].append(book)

            if len(sig_groups) == len(books):
                # All books have different content — these are different editions, skip entirely
                if verbose:
                    author_names = ', '.join(books[0].authors.values_list('name', flat=True)) or 'Unknown'
                    self.stdout.write(
                        f'\n  SKIP: {books[0].title[:50]} by {author_names} '
                        f'({len(books)} editions, all different content)'
                    )
                skipped_different += 1
                continue

            # Process each sub-group of truly identical books
            for sig, identical_books in sig_groups.items():
                if len(identical_books) < 2:
                    continue  # Only one book with this signature, nothing to dedup

                # Score each identical book
                scored = []
                for book in identical_books:
                    score = (
                        book.user_books.count() * 100
                        + book.quotes.count() * 10
                        + book.study_notes.count() * 10
                        + (10 if hasattr(book, 'dna') and book.dna else 0)
                        + (5 if book.book_group_id else 0)
                        + (5 if book.cover_image else 0)
                        + (3 if book.description else 0)
                        + (2 if book.pages else 0)
                        + (1 if book.isbn else 0)
                    )
                    scored.append((score, book))

                scored.sort(key=lambda x: (-x[0], x[1].id))

                keeper = scored[0][1]
                to_delete = [s[1] for s in scored[1:]]

                if verbose:
                    author_names = ', '.join(keeper.authors.values_list('name', flat=True)) or 'Unknown'
                    self.stdout.write(
                        f'\n--- {keeper.title[:60]} by {author_names} '
                        f'({len(identical_books)} identical copies) ---'
                    )
                    self.stdout.write(f'  Keeping: ID {keeper.id} (score={scored[0][0]})')
                    for s, b in scored[1:]:
                        self.stdout.write(f'  Deleting: ID {b.id} (score={s})')

                if dry_run:
                    total_deleted += len(to_delete)
                    continue

                for book in to_delete:
                    with transaction.atomic():
                        post_delete.disconnect(
                            reading_models.update_quotes_count_on_delete,
                            sender=Quote
                        )

                        try:
                            # 1. Transfer UserBooks
                            for ub in book.user_books.all():
                                existing = UserBook.objects.filter(
                                    user=ub.user, book=keeper
                                ).first()

                                if existing:
                                    for field in ('rating', 'review', 'started_at', 'finished_at',
                                                  'current_page', 'depth_score'):
                                        dup_val = getattr(ub, field, None)
                                        if dup_val and not getattr(existing, field, None):
                                            setattr(existing, field, dup_val)
                                    if ub.is_favorite and not existing.is_favorite:
                                        existing.is_favorite = True
                                    if ub.is_owned and not existing.is_owned:
                                        existing.is_owned = True
                                    existing.save()

                                    Quote.objects.filter(user_book=ub).update(
                                        user_book=existing, book=keeper
                                    )
                                    StudyNote.objects.filter(user_book=ub).update(
                                        user_book=existing, book=keeper
                                    )
                                    ub.delete()
                                else:
                                    ub.book = keeper
                                    ub.save()
                                stats['userbooks'] += 1

                            # 2. Transfer remaining Quotes
                            remaining_quotes = book.quotes.all()
                            count = remaining_quotes.count()
                            if count:
                                remaining_quotes.update(book=keeper, book_title=keeper.title)
                                stats['quotes'] += count

                            # 3. Transfer StudyNotes
                            remaining_notes = book.study_notes.all()
                            count = remaining_notes.count()
                            if count:
                                remaining_notes.update(book=keeper)
                                stats['study_notes'] += count

                            # 4. Transfer VocabularyWords
                            vocab = VocabularyWord.objects.filter(book=book)
                            count = vocab.count()
                            if count:
                                vocab.update(book=keeper)
                                stats['vocabulary'] += count

                            # 5. Transfer ReadingListItems
                            if ReadingListItem:
                                for item in ReadingListItem.objects.filter(book=book):
                                    exists = ReadingListItem.objects.filter(
                                        reading_list=item.reading_list, book=keeper
                                    ).exists()
                                    if exists:
                                        item.delete()
                                    else:
                                        item.book = keeper
                                        item.save()
                                    stats['list_items'] += 1

                            # 6. Transfer JournalEntries
                            if JournalEntry:
                                count = JournalEntry.objects.filter(book=book).update(book=keeper)
                                stats['journal'] += count

                            # 7. Transfer BookDNAVotes
                            for vote in BookDNAVote.objects.filter(book=book):
                                exists = BookDNAVote.objects.filter(
                                    user=vote.user, book=keeper
                                ).exists()
                                if exists:
                                    vote.delete()
                                else:
                                    vote.book = keeper
                                    vote.save()
                                stats['dna_votes'] += 1

                            # 8. Transfer book_group if keeper doesn't have one
                            if book.book_group_id and not keeper.book_group_id:
                                keeper.book_group = book.book_group
                                keeper.save(update_fields=['book_group'])
                                stats['book_groups'] += 1

                            # Delete the duplicate
                            book.delete()

                        finally:
                            post_delete.connect(
                                reading_models.update_quotes_count_on_delete,
                                sender=Quote
                            )

                    total_deleted += 1

        # Summary
        self.stdout.write('\n' + '=' * 50)
        label = 'Would delete' if dry_run else 'Deleted'
        self.stdout.write(self.style.SUCCESS(f'{label} {total_deleted} truly identical duplicates'))
        if skipped_different:
            self.stdout.write(f'Skipped {skipped_different} groups (different editions)')
        if any(stats.values()):
            transfer_label = 'Would transfer' if dry_run else 'Transferred'
            for key, count in stats.items():
                if count:
                    self.stdout.write(f'  {transfer_label} {count} {key}')
        self.stdout.write('=' * 50)
