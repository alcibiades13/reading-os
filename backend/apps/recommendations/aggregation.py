"""
Aggregation functions for Book DNA and User Taste Profile.
These run synchronously when a user submits a survey.
"""
import math
from collections import Counter
from django.db.models import Avg, Q
from django.utils import timezone
from apps.books.models import Book, BookDNA, BookDNAVote, BookGroupDNA, Author, Genre
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

    # Aggregate primary themes (most commonly marked as primary)
    all_primary_themes = []
    for vote in votes:
        all_primary_themes.extend(vote.primary_themes or [])
    primary_theme_counts = Counter(all_primary_themes)
    top_primary_themes = [t for t, _ in primary_theme_counts.most_common(3)]

    # Aggregate genre tags
    all_genre_tags = []
    for vote in votes:
        all_genre_tags.extend(vote.genre_tags or [])
    genre_tag_counts = Counter(all_genre_tags)
    min_genre_count = max(1, votes.count() * 0.3)
    top_genre_tags = [
        tag for tag, count in genre_tag_counts.most_common(10)
        if count >= min_genre_count
    ]

    # Aggregate primary genre tag (most common)
    primary_genre_votes = [v.primary_genre_tag for v in votes if v.primary_genre_tag]
    primary_genre_tag = None
    if primary_genre_votes:
        primary_genre_tag = Counter(primary_genre_votes).most_common(1)[0][0]

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
            'primary_themes': top_primary_themes,
            'genre_tags': top_genre_tags,
            'primary_genre_tag': primary_genre_tag,
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

    # Aggregate themes affinity (primary themes get 3x weight)
    all_themes = []
    for vote in votes:
        all_themes.extend(vote.themes or [])
        # Primary themes count triple
        for pt in (vote.primary_themes or []):
            all_themes.extend([pt, pt])  # +2 extra = 3x total

    theme_counts = Counter(all_themes)
    top_themes = [theme for theme, _ in theme_counts.most_common(10)]
    taste_profile['themes_affinity'] = top_themes

    # Primary themes affinity
    all_primary_themes = []
    for vote in votes:
        all_primary_themes.extend(vote.primary_themes or [])
    primary_counts = Counter(all_primary_themes)
    taste_profile['primary_themes_affinity'] = [t for t, _ in primary_counts.most_common(5)]

    # Genre tags affinity (primary genre gets 3x weight)
    all_genre_tags = []
    for vote in votes:
        all_genre_tags.extend(vote.genre_tags or [])
        if vote.primary_genre_tag:
            all_genre_tags.extend([vote.primary_genre_tag, vote.primary_genre_tag])  # 3x total
    genre_counts = Counter(all_genre_tags)
    taste_profile['genre_tags_affinity'] = [t for t, _ in genre_counts.most_common(10)]

    # Primary genre tag affinity
    primary_genres = [v.primary_genre_tag for v in votes if v.primary_genre_tag]
    if primary_genres:
        taste_profile['primary_genre_tag_affinity'] = Counter(primary_genres).most_common(1)[0][0]
    else:
        taste_profile['primary_genre_tag_affinity'] = None

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


def compute_reading_taste(user_id: int, scope: str = 'all') -> dict:
    """
    Compute reading taste from user's actual books (not survey votes).
    Derives top genres, authors, themes, and DNA vector from book metadata.

    Args:
        user_id: User ID
        scope: 'all' (read + owned), 'owned' (only owned books)
    """
    user = User.objects.get(id=user_id)

    # Build filter based on scope
    base_q = Q(user=user)
    if scope == 'owned':
        base_q &= Q(is_owned=True)
    else:
        base_q &= (Q(status='read') | Q(is_owned=True))

    user_books = list(
        UserBook.objects.filter(base_q)
        .select_related('book', 'book__publisher')
        .prefetch_related('book__authors', 'book__genres')
    )

    if not user_books:
        return {
            'top_genres': [],
            'top_authors': [],
            'top_themes': [],
            'top_genre_tags': [],
            'dna_vector': {},
            'books_count': 0,
            'books_with_dna': 0,
            'scope': scope,
        }

    # Prefetch DNA data in bulk (avoid N+1)
    book_ids = [ub.book_id for ub in user_books]
    book_dna_map = {
        dna.book_id: dna
        for dna in BookDNA.objects.filter(book_id__in=book_ids)
    }
    group_ids = [ub.book.book_group_id for ub in user_books if ub.book.book_group_id]
    group_dna_map = {
        dna.book_group_id: dna
        for dna in BookGroupDNA.objects.filter(book_group_id__in=group_ids)
    } if group_ids else {}

    def get_dna(book):
        if book.book_group_id and book.book_group_id in group_dna_map:
            return group_dna_map[book.book_group_id]
        return book_dna_map.get(book.id)

    def get_weight(ub):
        w = 1.0
        if ub.is_favorite:
            w *= 2.0
        if ub.rating:
            w *= (float(ub.rating) / 10.0) + 0.5
        if ub.quotes_count > 0:
            w *= 1.0 + (math.log1p(ub.quotes_count) * 0.3)
        return w

    # Aggregate
    genre_counter = Counter()
    author_counter = Counter()
    author_books_count = Counter()
    author_pages = Counter()
    theme_counter = Counter()
    genre_tag_counter = Counter()
    dna_attributes = ['pace', 'complexity', 'emotional_intensity',
                      'darkness', 'character_focus', 'introspection']
    dna_weighted_sums = {attr: 0.0 for attr in dna_attributes}
    dna_total_weight = 0.0
    books_with_dna = 0

    for ub in user_books:
        w = get_weight(ub)

        for genre in ub.book.genres.all():
            genre_counter[genre.id] += w

        for author in ub.book.authors.all():
            # Resolve to canonical (primary) author if grouped
            canonical_id = author.id
            if author.author_group_id:
                primary = author.author_group.get_primary_author()
                if primary:
                    canonical_id = primary.id
            author_counter[canonical_id] += w
            author_books_count[canonical_id] += 1
            author_pages[canonical_id] += ub.book.pages or 0

        dna = get_dna(ub.book)
        if dna:
            books_with_dna += 1
            dna_total_weight += w

            for attr in dna_attributes:
                val = getattr(dna, attr, None)
                if val is not None:
                    dna_weighted_sums[attr] += float(val) * w

            for theme in (dna.themes or []):
                theme_counter[theme] += w
            for pt in (dna.primary_themes or []):
                theme_counter[pt] += w  # extra weight for primary

            for gt in (dna.genre_tags or []):
                genre_tag_counter[gt] += w
            if dna.primary_genre_tag:
                genre_tag_counter[dna.primary_genre_tag] += w

    # Resolve top genres
    top_genre_ids = [gid for gid, _ in genre_counter.most_common(8)]
    genres = {g.id: g for g in Genre.objects.filter(id__in=top_genre_ids)}
    top_genres = [
        {'id': gid, 'name': genres[gid].name, 'slug': genres[gid].slug,
         'score': round(genre_counter[gid], 2)}
        for gid in top_genre_ids if gid in genres
    ]

    # Resolve top authors
    top_author_ids = [aid for aid, _ in author_counter.most_common(10)]
    authors = {a.id: a for a in Author.objects.filter(id__in=top_author_ids)}
    top_authors = [
        {'id': aid, 'name': authors[aid].name, 'slug': authors[aid].slug,
         'score': round(author_counter[aid], 2),
         'books_count': author_books_count[aid],
         'total_pages': author_pages[aid]}
        for aid in top_author_ids if aid in authors
    ]

    # Top themes and genre tags
    top_themes = [t for t, _ in theme_counter.most_common(10)]
    top_genre_tags = [t for t, _ in genre_tag_counter.most_common(8)]

    # DNA vector
    dna_vector = {}
    if dna_total_weight > 0:
        for attr in dna_attributes:
            dna_vector[attr] = round(dna_weighted_sums[attr] / dna_total_weight, 3)

    return {
        'top_genres': top_genres,
        'top_authors': top_authors,
        'top_themes': top_themes,
        'top_genre_tags': top_genre_tags,
        'dna_vector': dna_vector,
        'books_count': len(user_books),
        'books_with_dna': books_with_dna,
        'scope': scope,
    }
