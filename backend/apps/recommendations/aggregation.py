"""
Aggregation functions for Book DNA and User Taste Profile.
These run synchronously when a user submits a survey.
"""
from collections import Counter
from django.db.models import Avg
from django.utils import timezone
from apps.books.models import Book, BookDNA, BookDNAVote
from apps.reading.models import UserBook
from apps.users.models import User


def aggregate_book_dna(book_id: int) -> BookDNA:
    """
    Aggregate all votes for a book and update its BookDNA.
    Called when a user submits a survey for this book.
    """
    book = Book.objects.get(id=book_id)
    votes = BookDNAVote.objects.filter(book=book)

    if not votes.exists():
        # No votes yet, create default DNA if doesn't exist
        dna, created = BookDNA.objects.get_or_create(
            book=book,
            defaults={'source': 'manual'}
        )
        return dna

    # Calculate averages for each attribute
    aggregations = votes.aggregate(
        pace=Avg('pace'),
        complexity=Avg('complexity'),
        emotional_intensity=Avg('emotional_intensity'),
        darkness=Avg('darkness'),
        character_focus=Avg('character_focus'),
        introspection=Avg('introspection'),
    )

    # Aggregate themes (most common)
    all_themes = []
    for vote in votes:
        all_themes.extend(vote.themes or [])

    theme_counts = Counter(all_themes)
    # Get themes that appear in at least 30% of votes (min 1)
    min_count = max(1, votes.count() * 0.3)
    top_themes = [theme for theme, count in theme_counts.most_common(10) if count >= min_count]

    # Calculate confidence score based on vote count
    # 1 vote = 0.1, 5 votes = 0.5, 10+ votes = 1.0
    vote_count = votes.count()
    confidence = min(vote_count / 10.0, 1.0)

    # Update or create BookDNA
    dna, created = BookDNA.objects.update_or_create(
        book=book,
        defaults={
            'pace': aggregations['pace'] or 0.5,
            'complexity': aggregations['complexity'] or 0.5,
            'emotional_intensity': aggregations['emotional_intensity'] or 0.5,
            'darkness': aggregations['darkness'] or 0.5,
            'character_focus': aggregations['character_focus'] or 0.5,
            'introspection': aggregations['introspection'] or 0.5,
            'themes': top_themes,
            'source': 'user_votes',
            'vote_count': vote_count,
            'confidence_score': confidence,
        }
    )

    return dna


def update_user_taste_profile(user_id: int) -> dict:
    """
    Calculate User Taste Vector from all their votes.
    Uses weighted average with more weight on recent votes.
    Called when a user submits a survey.
    """
    user = User.objects.get(id=user_id)
    votes = BookDNAVote.objects.filter(user=user).order_by('-created_at')

    if not votes.exists():
        return user.reading_dna or {}

    # Initialize weighted sums
    attributes = ['pace', 'complexity', 'emotional_intensity',
                  'darkness', 'character_focus', 'introspection']

    weighted_sums = {attr: 0.0 for attr in attributes}
    weighted_counts = {attr: 0.0 for attr in attributes}

    # Calculate weighted averages (newer votes have higher weight)
    for idx, vote in enumerate(votes):
        # Exponential decay: weight = 1 / (index + 1)
        weight = 1.0 / (idx + 1)

        for attr in attributes:
            value = getattr(vote, attr)
            if value is not None:
                weighted_sums[attr] += value * weight
                weighted_counts[attr] += weight

    # Calculate final preferences
    taste_profile = {}
    preference_mapping = {
        'pace': 'pace_preference',
        'complexity': 'complexity_tolerance',
        'emotional_intensity': 'emotional_preference',
        'darkness': 'darkness_tolerance',
        'character_focus': 'character_focus_preference',
        'introspection': 'introspection_preference',
    }

    for attr in attributes:
        if weighted_counts[attr] > 0:
            taste_profile[preference_mapping[attr]] = weighted_sums[attr] / weighted_counts[attr]
        else:
            taste_profile[preference_mapping[attr]] = 0.5

    # Aggregate themes affinity
    all_themes = []
    for vote in votes:
        all_themes.extend(vote.themes or [])

    theme_counts = Counter(all_themes)
    top_themes = [theme for theme, _ in theme_counts.most_common(10)]
    taste_profile['themes_affinity'] = top_themes

    # Add implicit signals from UserBook data
    user_books = UserBook.objects.filter(user=user)
    taste_profile['books_completed'] = user_books.filter(status='read').count()
    taste_profile['books_abandoned'] = user_books.filter(status='abandoned').count()
    taste_profile['books_in_progress'] = user_books.filter(status='currently_reading').count()

    # Calculate completion rate
    total = taste_profile['books_completed'] + taste_profile['books_abandoned']
    if total > 0:
        taste_profile['completion_rate'] = taste_profile['books_completed'] / total
    else:
        taste_profile['completion_rate'] = 1.0

    # Add metadata
    taste_profile['last_updated'] = timezone.now().isoformat()
    taste_profile['vote_count'] = votes.count()

    # Update user's reading_dna
    user.reading_dna = taste_profile
    user.save(update_fields=['reading_dna'])

    return taste_profile


def get_user_taste_profile(user: User) -> dict:
    """
    Get formatted user taste profile for API response.
    """
    dna = user.reading_dna or {}

    return {
        'pace_preference': dna.get('pace_preference', 0.5),
        'complexity_tolerance': dna.get('complexity_tolerance', 0.5),
        'emotional_preference': dna.get('emotional_preference', 0.5),
        'darkness_tolerance': dna.get('darkness_tolerance', 0.5),
        'character_focus_preference': dna.get('character_focus_preference', 0.5),
        'introspection_preference': dna.get('introspection_preference', 0.5),
        'themes_affinity': dna.get('themes_affinity', []),
        'books_completed': dna.get('books_completed', 0),
        'books_abandoned': dna.get('books_abandoned', 0),
        'completion_rate': dna.get('completion_rate', 1.0),
        'vote_count': dna.get('vote_count', 0),
        'last_updated': dna.get('last_updated'),
    }
