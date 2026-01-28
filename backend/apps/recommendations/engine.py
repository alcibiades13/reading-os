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

            results.append({
                'book': dna.book,
                'match_score': round(adjusted_score * 100, 1),
                'reason': 'content_based',
                'dna': dna,
            })

        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)

        return results[:limit]

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
            book_themes = dna.themes or []
            matching_themes = set(themes) & set(book_themes)

            if matching_themes:
                results.append({
                    'book': dna.book,
                    'matching_themes': list(matching_themes),
                    'theme_match_count': len(matching_themes),
                    'dna': dna,
                })

        # Sort by number of matching themes
        results.sort(key=lambda x: x['theme_match_count'], reverse=True)

        return results[:limit]

    def get_similar_books(self, book: Book, limit: int = 6) -> List[Dict[str, Any]]:
        """Get books similar to a given book based on its DNA."""
        try:
            book_dna = book.dna
        except BookDNA.DoesNotExist:
            return []

        book_vector = book_dna.to_vector()

        # Get all other books with DNA (don't exclude user's library for similar books)
        other_books = BookDNA.objects.exclude(
            book_id=book.id
        ).filter(
            vote_count__gte=1
        ).select_related('book')

        results = []
        for dna in other_books:
            similarity = cosine_similarity(book_vector, dna.to_vector())

            # Also consider theme overlap
            book_themes = set(book_dna.themes or [])
            other_themes = set(dna.themes or [])
            theme_overlap = len(book_themes & other_themes) / max(len(book_themes | other_themes), 1)

            # Combined score: 70% DNA similarity, 30% theme overlap
            combined_score = 0.7 * similarity + 0.3 * theme_overlap

            results.append({
                'book': dna.book,
                'similarity_score': round(combined_score * 100, 1),
                'dna_similarity': round(similarity * 100, 1),
                'theme_overlap': round(theme_overlap * 100, 1),
            })

        results.sort(key=lambda x: x['similarity_score'], reverse=True)

        return results[:limit]
