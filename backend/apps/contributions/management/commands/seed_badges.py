from django.core.management.base import BaseCommand

from apps.contributions.models import Badge


BADGES = [
    # Activity badges
    {
        'slug': 'first_quote',
        'name': 'First Mark',
        'description': 'Added your first quote to the library.',
        'icon': 'quote',
        'color': '#6366f1',
        'category': 'activity',
        'auto_criteria': {'action': 'quote_added', 'count': 1},
    },
    {
        'slug': 'century_quotes',
        'name': 'Century Scribe',
        'description': 'Added 100 quotes to the library.',
        'icon': 'scroll-text',
        'color': '#6366f1',
        'category': 'activity',
        'auto_criteria': {'action': 'quote_added', 'count': 100},
    },
    {
        'slug': 'first_review',
        'name': 'First Impression',
        'description': 'Wrote your first book review.',
        'icon': 'pen-line',
        'color': '#8b5cf6',
        'category': 'activity',
        'auto_criteria': {'action': 'review_written', 'count': 1},
    },
    {
        'slug': 'bookworm_25',
        'name': 'Bookworm',
        'description': 'Finished reading 25 books.',
        'icon': 'book-open',
        'color': '#10b981',
        'category': 'activity',
        'auto_criteria': {'action': 'book_finished', 'count': 25},
    },
    {
        'slug': 'deep_reader',
        'name': 'Deep Reader',
        'description': 'Created 50 study notes.',
        'icon': 'sparkles',
        'color': '#0ea5e9',
        'category': 'activity',
        'auto_criteria': {'action': 'study_note_added', 'count': 50},
    },

    # Curation badges
    {
        'slug': 'literary_cartographer',
        'name': 'Literary Cartographer',
        'description': 'Linked 50 author records across the library.',
        'icon': 'map',
        'color': '#f59e0b',
        'category': 'activity',
        'auto_criteria': {'action': 'author_linked', 'count': 50},
    },
    {
        'slug': 'data_guardian',
        'name': 'Data Guardian',
        'description': 'Resolved 25 data quality issues.',
        'icon': 'shield-check',
        'color': '#10b981',
        'category': 'activity',
        'auto_criteria': {'action': 'data_issue_resolved', 'count': 25},
    },

    # Quality badges
    {
        'slug': 'trusted_voice',
        'name': 'Trusted Voice',
        'description': 'Maintained 95%+ quality ratio over 100+ contributions.',
        'icon': 'badge-check',
        'color': '#10b981',
        'category': 'quality',
        'auto_criteria': {'quality_ratio_min': 0.95, 'min_contributions': 100},
    },

    # Special badges (manual)
    {
        'slug': 'founding_mapper',
        'name': 'Founding Mapper',
        'description': 'An early contributor who helped map the literary universe.',
        'icon': 'compass',
        'color': '#f59e0b',
        'category': 'founding',
        'auto_criteria': None,
    },
    {
        'slug': 'founding_member',
        'name': 'Founding Member',
        'description': 'One of the original members of the community.',
        'icon': 'star',
        'color': '#eab308',
        'category': 'founding',
        'auto_criteria': None,
    },

    # Tier badges (auto on promotion)
    {
        'slug': 'tier_contributor',
        'name': 'Contributor',
        'description': 'Reached the Contributor tier through consistent participation.',
        'icon': 'user-plus',
        'color': '#6366f1',
        'category': 'activity',
        'auto_criteria': {'tier': 'contributor'},
    },
    {
        'slug': 'tier_curator',
        'name': 'Curator',
        'description': 'Reached the Curator tier through dedicated data curation.',
        'icon': 'library',
        'color': '#8b5cf6',
        'category': 'activity',
        'auto_criteria': {'tier': 'curator'},
    },
    {
        'slug': 'tier_moderator',
        'name': 'Moderator',
        'description': 'Trusted community moderator.',
        'icon': 'shield',
        'color': '#ef4444',
        'category': 'activity',
        'auto_criteria': {'tier': 'moderator'},
    },
]


class Command(BaseCommand):
    help = 'Seed initial badge definitions'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for badge_data in BADGES:
            slug = badge_data['slug']
            obj, created = Badge.objects.update_or_create(
                slug=slug,
                defaults=badge_data,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Badges seeded: {created_count} created, {updated_count} updated'
            )
        )
