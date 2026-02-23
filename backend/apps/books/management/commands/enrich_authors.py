"""
Management command to enrich Author records with bio, photo, and dates
from Open Library, Wikipedia, and Wikidata.

Usage:
    python manage.py enrich_authors                  # All authors missing data
    python manage.py enrich_authors --ids 1 2 3      # Specific author IDs
    python manage.py enrich_authors --name "Tolkien"  # Search by name
    python manage.py enrich_authors --force           # Overwrite existing data
    python manage.py enrich_authors --dry-run         # Preview without saving
"""

import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.books.models import Author
from apps.books.author_enrichment import enrich_author


class Command(BaseCommand):
    help = 'Enrich author records with bio, photo, and dates from Open Library + Wikipedia + Wikidata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ids', nargs='+', type=int,
            help='Specific author IDs to enrich',
        )
        parser.add_argument(
            '--name', type=str,
            help='Filter authors by name (contains)',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Overwrite existing bio/photo/dates',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview what would be updated without saving',
        )
        parser.add_argument(
            '--delay', type=float, default=1.0,
            help='Delay between API calls in seconds (default: 1.0)',
        )
        parser.add_argument(
            '--limit', type=int, default=0,
            help='Max number of authors to process (0 = all)',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        delay = options['delay']
        limit = options['limit']

        qs = Author.objects.all()

        if options['ids']:
            qs = qs.filter(id__in=options['ids'])
        elif options['name']:
            qs = qs.filter(name__icontains=options['name'])
        elif not force:
            qs = qs.filter(
                Q(bio='') | Q(photo='') | Q(birth_date__isnull=True)
            )

        qs = qs.order_by('name')
        if limit:
            qs = qs[:limit]

        authors = list(qs)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nAuthor Enrichment {"(DRY RUN)" if dry_run else ""}'
        ))
        self.stdout.write(f'  Authors to process: {len(authors)}')
        self.stdout.write(f'  Force overwrite: {force}\n')

        stats = {'updated': 0, 'skipped': 0, 'errors': 0}

        for i, author in enumerate(authors, 1):
            self.stdout.write(f'[{i}/{len(authors)}] {author.name} (id={author.id})')

            try:
                if dry_run:
                    self.stdout.write('  [DRY RUN] would attempt enrichment')
                    stats['skipped'] += 1
                    continue

                updated_fields = enrich_author(author, force=force)
                if updated_fields:
                    for key, val in updated_fields.items():
                        display = str(val)
                        if len(display) > 80:
                            display = display[:80] + '...'
                        self.stdout.write(self.style.SUCCESS(f'  {key}: {display}'))
                    stats['updated'] += 1
                else:
                    self.stdout.write('  No new data found')
                    stats['skipped'] += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {e}'))
                stats['errors'] += 1

            if i < len(authors):
                time.sleep(delay)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Updated:  {stats["updated"]}'))
        self.stdout.write(f'Skipped:  {stats["skipped"]}')
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'Errors:   {stats["errors"]}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
