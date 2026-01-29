from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.books.models import Book, BookGroup
from difflib import SequenceMatcher


class Command(BaseCommand):
    help = 'Find and link potential editions of the same book'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Automatically link high-confidence matches (>= 0.90 similarity)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show matches without creating links',
        )
        parser.add_argument(
            '--min-similarity',
            type=float,
            default=0.80,
            help='Minimum similarity score to consider (0.0-1.0, default: 0.80)',
        )

    def handle(self, *args, **options):
        auto_link = options['auto']
        dry_run = options['dry_run']
        min_similarity = options['min_similarity']

        self.stdout.write(self.style.SUCCESS('Finding potential editions...'))
        self.stdout.write(f'Min similarity: {min_similarity}')
        self.stdout.write(f'Auto-link: {auto_link} (>= 0.90)')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write('')

        # Get all books without groups or with single-edition groups
        books = Book.objects.prefetch_related('authors', 'publisher', 'book_group__editions')

        processed = set()
        total_matches = 0
        total_linked = 0

        for book in books:
            # Skip if already processed
            if book.id in processed:
                continue

            # Skip if already in multi-edition group
            if book.book_group and book.book_group.editions.count() > 1:
                processed.add(book.id)
                continue

            # Find potential editions
            matches = self._find_potential_editions(book, min_similarity)

            if not matches:
                processed.add(book.id)
                continue

            # Display matches
            self.stdout.write(self.style.WARNING(f'\n📚 Book: {book.title} (ID: {book.id})'))
            if book.authors.exists():
                authors = ', '.join([a.name for a in book.authors.all()])
                self.stdout.write(f'   Authors: {authors}')
            self.stdout.write(f'   ISBN: {book.isbn or "N/A"} | Language: {book.language or "N/A"}\n')

            for match in matches:
                total_matches += 1
                match_book = match['book']
                similarity = match['similarity']

                self.stdout.write(
                    f'   ➜ Match (score: {similarity:.2f}): '
                    f'{match_book.title} (ID: {match_book.id})'
                )
                if match_book.authors.exists():
                    authors = ', '.join([a.name for a in match_book.authors.all()])
                    self.stdout.write(f'     Authors: {authors}')
                self.stdout.write(
                    f'     ISBN: {match_book.isbn or "N/A"} | '
                    f'Language: {match_book.language or "N/A"}'
                )

                # Auto-link high confidence matches
                if auto_link and similarity >= 0.90 and not dry_run:
                    self._link_books(book, match_book)
                    total_linked += 1
                    self.stdout.write(self.style.SUCCESS('     ✓ Automatically linked'))
                elif auto_link and similarity >= 0.90:
                    self.stdout.write(self.style.SUCCESS('     ✓ Would auto-link (dry run)'))

            # Mark all matches as processed
            processed.add(book.id)
            for match in matches:
                processed.add(match['book'].id)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Total potential matches found: {total_matches}')
        if auto_link and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Total books automatically linked: {total_linked}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def _find_potential_editions(self, book, min_similarity):
        """Find potential editions for a given book"""
        author_names = set(author.name.lower().strip() for author in book.authors.all())

        if not author_names:
            return []

        # Find candidates
        candidates_qs = Book.objects.exclude(id=book.id)

        # Only exclude same book_group if book has a group
        if book.book_group:
            candidates_qs = candidates_qs.exclude(book_group=book.book_group)

        candidates = candidates_qs.prefetch_related('authors')

        matches = []
        book_title_lower = book.title.lower().strip()

        for candidate in candidates:
            candidate_author_names = set(
                author.name.lower().strip() for author in candidate.authors.all()
            )

            if not candidate_author_names:
                continue

            # Calculate author similarity
            author_overlap = len(author_names & candidate_author_names)
            author_similarity = 0.0

            if author_overlap > 0:
                author_similarity = 1.0
            else:
                # Check for similar author names
                max_author_sim = 0.0
                for author1 in author_names:
                    for author2 in candidate_author_names:
                        sim = SequenceMatcher(None, author1, author2).ratio()
                        max_author_sim = max(max_author_sim, sim)
                author_similarity = max_author_sim

            # Skip if authors are too different
            if author_similarity < 0.75:
                continue

            # Calculate title similarity
            candidate_title_lower = candidate.title.lower().strip()
            title_similarity = SequenceMatcher(
                None, book_title_lower, candidate_title_lower
            ).ratio()

            # Combined score
            combined_score = (title_similarity * 0.7) + (author_similarity * 0.3)

            if combined_score >= min_similarity:
                # Check if ISBNs are different (or missing)
                isbn_different = True
                if book.isbn and candidate.isbn:
                    isbn_different = book.isbn != candidate.isbn

                if isbn_different:
                    matches.append({
                        'book': candidate,
                        'similarity': combined_score,
                        'title_similarity': title_similarity,
                        'author_similarity': author_similarity,
                    })

        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches

    def _link_books(self, book1, book2):
        """Link two books as editions"""
        # If either has a group, use that; else create new
        if book1.book_group:
            group = book1.book_group
        elif book2.book_group:
            group = book2.book_group
        else:
            # Create new group
            group = BookGroup.objects.create(canonical_title=book1.title)
            group.canonical_authors.set(book1.authors.all())
            book1.is_primary_edition = True

        # Link both books
        book1.book_group = group
        book2.book_group = group
        book1.save()
        book2.save()

        # Update stats
        group.update_stats()

        return group
