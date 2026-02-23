"""
Recommendation Engine for book recommendations.
Uses cosine similarity between User Taste Vector and Book DNA.
"""
import math
from typing import List, Dict, Any, Optional
from django.db.models import Q, Avg
from apps.books.models import Book, BookDNA
from apps.reading.models import UserBook
from apps.users.models import User


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


class RecommendationEngine:
    """
    Recommendation engine that uses:
    1. Cosine similarity between User Taste Vector and Book DNA
    2. Contextual filtering based on mood
    3. Theme-based matching
    """

    VECTOR_ATTRIBUTES = [
        'pace', 'complexity', 'emotional_intensity',
        'darkness', 'character_focus', 'introspection'
    ]

    # Contextual filters for different moods
    CONTEXT_FILTERS = {
        'peaceful': {
            'pace__lte': 0.4,
            'darkness__lte': 0.3,
            'emotional_intensity__lte': 0.4,
        },
        'challenge': {
            'complexity__gte': 0.7,
            'introspection__gte': 0.6,
        },
        'emotional': {
            'emotional_intensity__gte': 0.7,
        },
        'quick': {
            'pace__gte': 0.6,
        },
        'light': {
            'darkness__lte': 0.3,
            'complexity__lte': 0.4,
        },
        'deep': {
            'introspection__gte': 0.7,
            'complexity__gte': 0.6,
        },
    }

    def __init__(self, user: User):
        self.user = user
        self.user_taste = self._get_user_taste_vector()
        self.excluded_book_ids = self._get_excluded_books()

    def _get_user_taste_vector(self) -> List[float]:
        """Extract user taste vector from reading_dna."""
        dna = self.user.reading_dna or {}
        return [
            dna.get('pace_preference', 0.5),
            dna.get('complexity_tolerance', 0.5),
            dna.get('emotional_preference', 0.5),
            dna.get('darkness_tolerance', 0.5),
            dna.get('character_focus_preference', 0.5),
            dna.get('introspection_preference', 0.5),
        ]

    def _get_excluded_books(self) -> List[int]:
        """Get book IDs that user should not see in recommendations."""
        return list(UserBook.objects.filter(
            user=self.user,
            status__in=['read', 'currently_reading', 'abandoned', 'want_to_read']
        ).values_list('book_id', flat=True))

    def _has_valid_taste_profile(self) -> bool:
        """Check if user has a meaningful taste profile."""
        dna = self.user.reading_dna or {}
        # Check if any preference exists and is not default 0.5
        for key in ['pace_preference', 'complexity_tolerance', 'emotional_preference',
                    'darkness_tolerance', 'character_focus_preference', 'introspection_preference']:
            value = dna.get(key)
            if value is not None and value != 0.5:
                return True
        return False

    def get_content_based_recommendations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Main recommendation: Cosine similarity between user taste and book DNA.
        Falls back to popular books if user has no taste profile.
        """
        # Get all books with DNA that user hasn't seen
        books_with_dna = BookDNA.objects.exclude(
            book_id__in=self.excluded_book_ids
        ).filter(
            confidence_score__gte=0.1  # Minimum confidence threshold
        ).select_related('book')

        if not books_with_dna.exists():
            # Fallback: return featured or recent books
            return self._get_fallback_recommendations(limit)

        # If user has no taste profile, return diverse selection
        if not self._has_valid_taste_profile():
            return self._get_diverse_recommendations(books_with_dna, limit)

        # Calculate similarity scores
        results = []
        for dna in books_with_dna:
            book_vector = dna.to_vector()
            similarity = cosine_similarity(self.user_taste, book_vector)

            # Boost score based on confidence
            adjusted_score = similarity * (0.7 + 0.3 * dna.confidence_score)

            # Primary theme affinity boost
            user_primary = set((self.user.reading_dna or {}).get('primary_themes_affinity', []))
            book_primary = set(dna.primary_themes or [])
            primary_match = len(user_primary & book_primary)
            adjusted_score += primary_match * 0.05

            results.append({
                'book': dna.book,
                'match_score': round(adjusted_score * 100, 1),
                'reason': 'content_based',
                'dna': dna,
            })

        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)

        # Deduplicate by book_group: keep highest-scored edition
        seen_groups = set()
        deduped = []
        for rec in results:
            group_id = rec['book'].book_group_id
            if group_id:
                if group_id in seen_groups:
                    continue
                seen_groups.add(group_id)
            deduped.append(rec)

        return deduped[:limit]

    def _get_fallback_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Get fallback recommendations when no DNA data available."""
        featured = Book.objects.filter(
            is_featured=True
        ).exclude(
            id__in=self.excluded_book_ids
        ).order_by('featured_order')[:limit]

        results = []
        for book in featured:
            results.append({
                'book': book,
                'match_score': 0,
                'reason': 'featured',
            })

        # If not enough featured, add recent books
        if len(results) < limit:
            recent = Book.objects.exclude(
                id__in=self.excluded_book_ids
            ).exclude(
                id__in=[r['book'].id for r in results]
            ).order_by('-created_at')[:limit - len(results)]

            for book in recent:
                results.append({
                    'book': book,
                    'match_score': 0,
                    'reason': 'recent',
                })

        return results

    def _get_diverse_recommendations(self, books_with_dna, limit: int) -> List[Dict[str, Any]]:
        """Get diverse recommendations for users without taste profile."""
        # Return books with high confidence scores (well-voted)
        books = books_with_dna.order_by('-confidence_score', '-vote_count')[:limit]

        results = []
        for dna in books:
            results.append({
                'book': dna.book,
                'match_score': round(dna.confidence_score * 100, 1),
                'reason': 'popular',
                'dna': dna,
            })

        return results

    def get_contextual_recommendations(self, context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get contextual recommendations based on mood.

        Contexts:
        - 'peaceful': light, slow, hopeful books
        - 'challenge': complex, demanding books
        - 'emotional': emotionally intense books
        - 'quick': fast-paced books
        - 'light': light, simple books
        - 'deep': introspective, philosophical books
        """
        context_filter = self.CONTEXT_FILTERS.get(context, {})

        books = BookDNA.objects.filter(**context_filter).exclude(
            book_id__in=self.excluded_book_ids
        ).filter(
            confidence_score__gte=0.1
        ).select_related('book').order_by('-confidence_score')[:limit]

        results = []
        for dna in books:
            results.append({
                'book': dna.book,
                'context': context,
                'match_score': round(dna.confidence_score * 100, 1),
                'dna': dna,
            })

        return results

    def get_theme_based_recommendations(self, themes: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Get recommendations based on themes."""
        if not themes:
            return []

        # Filter books that have any of the requested themes
        # Using JSONField contains lookup
        books = BookDNA.objects.exclude(
            book_id__in=self.excluded_book_ids
        ).filter(
            confidence_score__gte=0.1
        ).select_related('book')

        results = []
        for dna in books:
            book_themes = set(dna.themes or [])
            book_primary = set(dna.primary_themes or [])
            matching_themes = set(themes) & book_themes

            if matching_themes:
                # Primary matches count double
                matching_primary = set(themes) & book_primary
                matching_regular = matching_themes - matching_primary
                theme_score = len(matching_regular) + len(matching_primary) * 2

                results.append({
                    'book': dna.book,
                    'matching_themes': list(matching_themes),
                    'theme_match_count': theme_score,
                    'dna': dna,
                })

        # Sort by weighted theme match score
        results.sort(key=lambda x: x['theme_match_count'], reverse=True)

        return results[:limit]

    def get_similar_books(self, book: Book, limit: int = 6) -> List[Dict[str, Any]]:
        """Get books similar to a given book based on its DNA."""
        # Try to get DNA for this specific book
        book_dna = None
        try:
            book_dna = book.dna
        except BookDNA.DoesNotExist:
            pass

        # If no DNA for this book, check other editions in the same group
        if not book_dna and book.book_group_id:
            for edition in book.book_group.editions.exclude(id=book.id):
                try:
                    book_dna = edition.dna
                    break
                except BookDNA.DoesNotExist:
                    continue

        if not book_dna:
            return []

        book_vector = book_dna.to_vector()

        # Build list of book IDs to exclude (this book + other editions in the same group)
        excluded_ids = [book.id]
        if book.book_group_id:
            group_edition_ids = list(book.book_group.editions.values_list('id', flat=True))
            excluded_ids.extend(group_edition_ids)

        # Get all other books with DNA (include both user-voted and AI-populated)
        other_books = BookDNA.objects.exclude(
            book_id__in=excluded_ids
        ).select_related('book')

        results = []
        for dna in other_books:
            similarity = cosine_similarity(book_vector, dna.to_vector())

            # Also consider theme overlap with primary theme boost
            book_themes = set(book_dna.themes or [])
            other_themes = set(dna.themes or [])
            base_overlap = len(book_themes & other_themes) / max(len(book_themes | other_themes), 1)

            # Primary theme overlap bonus
            book_primary = set(book_dna.primary_themes or [])
            other_primary = set(dna.primary_themes or [])
            primary_bonus = len(book_primary & other_primary) * 0.1

            theme_overlap = min(base_overlap + primary_bonus, 1.0)

            # Combined score: 65% DNA similarity, 35% theme overlap
            combined_score = 0.65 * similarity + 0.35 * theme_overlap

            results.append({
                'book': dna.book,
                'similarity_score': round(combined_score * 100, 1),
                'dna_similarity': round(similarity * 100, 1),
                'theme_overlap': round(theme_overlap * 100, 1),
            })

        results.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Deduplicate by book_group: keep the edition with most votes
        seen_groups = set()
        deduped = []
        for rec in results:
            b = rec['book']
            group_id = b.book_group_id
            if group_id:
                if group_id in seen_groups:
                    continue
                seen_groups.add(group_id)
            deduped.append(rec)

        return deduped[:limit]


def get_discover_sections(user: User) -> dict:
    """
    Build personalized discover sections:
    - author_picks: books by user's favorite authors they haven't read
    - genre_picks: books in user's top genres they haven't read
    - because_you_read: similar books to a favorite/top-rated book
    """
    from .aggregation import compute_reading_taste
    from apps.books.serializers import BookListSerializer
    from apps.books.models import Author, Genre

    taste = compute_reading_taste(user.id, scope='all')

    # Books user already interacted with — exclude from recommendations
    excluded_ids = set(
        UserBook.objects.filter(user=user)
        .values_list('book_id', flat=True)
    )

    # --- Author picks ---
    author_picks = []
    for author_info in taste.get('top_authors', [])[:3]:
        try:
            author = Author.objects.get(id=author_info['id'])
        except Author.DoesNotExist:
            continue

        # Include books from all alias authors if grouped
        if author.author_group_id:
            author_ids = list(author.author_group.members.values_list('id', flat=True))
        else:
            author_ids = [author.id]

        books = (
            Book.objects.filter(authors__id__in=author_ids)
            .exclude(id__in=excluded_ids)
            .distinct()
            .select_related('publisher')
            .prefetch_related('authors', 'genres')
            .order_by('-created_at')[:6]
        )
        if books:
            author_picks.append({
                'author': {
                    'id': author.id,
                    'name': author.name,
                    'slug': author.slug,
                },
                'books': BookListSerializer(books, many=True).data,
            })

    # --- Genre picks ---
    genre_picks = []
    for genre_info in taste.get('top_genres', [])[:3]:
        try:
            genre = Genre.objects.get(id=genre_info['id'])
        except Genre.DoesNotExist:
            continue

        books = (
            Book.objects.filter(genres__id=genre.id)
            .exclude(id__in=excluded_ids)
            .select_related('publisher')
            .prefetch_related('authors', 'genres')
            .order_by('-created_at')[:8]
        )
        if books:
            genre_picks.append({
                'genre': {
                    'id': genre.id,
                    'name': genre.name,
                    'slug': genre.slug,
                },
                'books': BookListSerializer(books, many=True).data,
            })

    # --- Because you read ---
    because_you_read = []
    candidate_ubs = (
        UserBook.objects.filter(user=user, status='read')
        .select_related('book')
        .order_by('-is_favorite', '-rating', '-updated_at')[:10]
    )

    engine = RecommendationEngine(user)
    for ub in candidate_ubs:
        similar = engine.get_similar_books(ub.book, limit=20)
        # Filter out books already in user's library
        similar = [rec for rec in similar if rec['book'].id not in excluded_ids][:6]
        if similar:
            because_you_read.append({
                'source_book': BookListSerializer(ub.book).data,
                'similar': [
                    {**BookListSerializer(rec['book']).data,
                     'similarity_score': rec['similarity_score']}
                    for rec in similar
                ],
            })
            break  # Only one "because you read" section

    return {
        'author_picks': author_picks,
        'genre_picks': genre_picks,
        'because_you_read': because_you_read,
    }
