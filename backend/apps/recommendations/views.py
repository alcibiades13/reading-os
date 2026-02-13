from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.books.models import Book, BookDNA, BookDNAVote
from apps.books.serializers import BookListSerializer
from apps.reading.models import UserBook

from .engine import RecommendationEngine
from .aggregation import aggregate_book_dna, update_user_taste_profile, get_user_taste_profile
from .serializers import (
    SurveySubmitSerializer,
    TasteProfileSerializer,
    SurveyConfigSerializer,
    BookDNASerializer,
)
from .survey import SURVEY_QUESTIONS, THEME_OPTIONS, THEME_CATEGORIES, GENRE_TAG_OPTIONS

# Create theme ID to label mapping
THEME_LABELS = {t['id']: t['label'] for t in THEME_OPTIONS}


class RecommendationsView(APIView):
    """
    GET /api/recommendations/
    Returns personalized book recommendations for the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 50)  # Cap at 50

        engine = RecommendationEngine(request.user)
        recommendations = engine.get_content_based_recommendations(limit)

        # Get user preferences for highlighting matches
        user_dna = request.user.reading_dna or {}

        # Format response
        data = []
        for rec in recommendations:
            book_data = BookListSerializer(rec['book']).data
            book_data['match_score'] = rec['match_score']
            book_data['recommendation_reason'] = rec.get('reason', 'content_based')

            # Add DNA info if available
            dna = rec.get('dna')
            if dna:
                # Convert theme IDs to labels
                theme_labels = [THEME_LABELS.get(t, t) for t in (dna.themes or [])[:3]]
                book_data['themes'] = theme_labels

                # Find strongest match reasons based on user preferences
                match_highlights = []
                attr_labels = {
                    'pace': ('slow', 'fast'),
                    'complexity': ('light', 'dense'),
                    'emotional_intensity': ('calm', 'intense'),
                    'darkness': ('light', 'dark'),
                    'character_focus': ('plot-driven', 'character-driven'),
                    'introspection': ('action', 'introspective'),
                }
                user_pref_keys = {
                    'pace': 'pace_preference',
                    'complexity': 'complexity_tolerance',
                    'emotional_intensity': 'emotional_preference',
                    'darkness': 'darkness_tolerance',
                    'character_focus': 'character_focus_preference',
                    'introspection': 'introspection_preference',
                }

                for attr, (low_label, high_label) in attr_labels.items():
                    user_pref = user_dna.get(user_pref_keys[attr], 0.5)
                    book_val = getattr(dna, attr, 0.5)
                    # If user and book are aligned (both low or both high)
                    if abs(user_pref - book_val) < 0.25:
                        label = high_label if book_val > 0.5 else low_label
                        match_highlights.append(label)

                book_data['match_highlights'] = match_highlights[:2]  # Top 2 highlights

            data.append(book_data)

        return Response(data)


class ContextualRecommendationsView(APIView):
    """
    GET /api/recommendations/contextual/?context=peaceful
    Returns contextual recommendations based on mood.

    Available contexts:
    - peaceful: light, slow, hopeful books
    - challenge: complex, demanding books
    - emotional: emotionally intense books
    - quick: fast-paced books
    - light: light, simple books
    - deep: introspective, philosophical books
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        context = request.query_params.get('context', 'peaceful')
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 20)  # Cap at 20

        valid_contexts = ['peaceful', 'challenge', 'emotional', 'quick', 'light', 'deep']
        if context not in valid_contexts:
            return Response(
                {'error': f'Invalid context. Valid options: {", ".join(valid_contexts)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        engine = RecommendationEngine(request.user)
        recommendations = engine.get_contextual_recommendations(context, limit)

        data = []
        for rec in recommendations:
            book_data = BookListSerializer(rec['book']).data
            book_data['context'] = rec['context']
            book_data['match_score'] = rec.get('match_score', 0)
            data.append(book_data)

        return Response({
            'context': context,
            'books': data
        })


class SimilarBooksView(APIView):
    """
    GET /api/recommendations/similar/{book_id}/
    Returns books similar to the given book.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        limit = int(request.query_params.get('limit', 6))
        limit = min(limit, 12)

        # Debug: Check BookDNA status
        total_dna = BookDNA.objects.count()
        dna_with_votes = BookDNA.objects.filter(vote_count__gte=1).count()
        has_dna = hasattr(book, 'dna') and BookDNA.objects.filter(book=book).exists()
        print(f"[Similar] Book {book_id}: total_dna={total_dna}, with_votes={dna_with_votes}, has_dna={has_dna}")

        # Use engine if user is authenticated, otherwise basic similarity
        if request.user.is_authenticated:
            engine = RecommendationEngine(request.user)
        else:
            # Create engine with None user for anonymous access
            engine = RecommendationEngine.__new__(RecommendationEngine)
            engine.user = None
            engine.user_taste = [0.5] * 6
            engine.excluded_book_ids = []

        similar = engine.get_similar_books(book, limit)
        print(f"[Similar] Found {len(similar)} similar books")

        data = []
        for rec in similar:
            book_data = BookListSerializer(rec['book']).data
            book_data['similarity_score'] = rec['similarity_score']
            data.append(book_data)

        return Response(data)


class BookDNASurveyView(APIView):
    """
    POST /api/recommendations/survey/
    Submit a micro-survey for a book after reading.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SurveySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_id = serializer.validated_data['book_id']
        user_book_id = serializer.validated_data.get('user_book_id')
        responses = serializer.validated_data['responses']
        themes = serializer.validated_data.get('themes', [])

        # Get book
        book = get_object_or_404(Book, id=book_id)

        # Get user_book if provided
        user_book = None
        if user_book_id:
            user_book = get_object_or_404(UserBook, id=user_book_id, user=request.user)

        # Create or update vote
        vote, created = BookDNAVote.objects.update_or_create(
            user=request.user,
            book=book,
            defaults={
                'user_book': user_book,
                'pace': responses.get('pace'),
                'complexity': responses.get('complexity'),
                'emotional_intensity': responses.get('emotional_intensity'),
                'darkness': responses.get('darkness'),
                'character_focus': responses.get('character_focus'),
                'introspection': responses.get('introspection'),
                'themes': themes,
                'primary_themes': serializer.validated_data.get('primary_themes', []),
                'genre_tags': serializer.validated_data.get('genre_tags', []),
                'primary_genre_tag': serializer.validated_data.get('primary_genre_tag') or None,
            }
        )

        # Aggregate book DNA (synchronous)
        aggregate_book_dna(book_id)

        # Update user taste profile (synchronous)
        update_user_taste_profile(request.user.id)

        return Response({
            'success': True,
            'vote_id': vote.id,
            'created': created,
            'message': 'Survey submitted successfully'
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CheckSurveyView(APIView):
    """
    GET /api/recommendations/survey/check/{book_id}/
    Check if user has already voted for a book (or any edition in the same group).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, book_id):
        from apps.books.models import Book

        # Get the book and check its group
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'has_voted': False, 'vote': None})

        # Build query - check this book OR any book in the same group
        vote_query = Q(user=request.user, book_id=book_id)

        if book.book_group_id:
            # Also check votes for other editions in the same group
            group_book_ids = book.book_group.editions.values_list('id', flat=True)
            vote_query = Q(user=request.user, book_id__in=group_book_ids)

        has_voted = BookDNAVote.objects.filter(vote_query).exists()

        vote_data = None
        if has_voted:
            vote = BookDNAVote.objects.filter(vote_query).first()
            vote_data = {
                'pace': vote.pace,
                'complexity': vote.complexity,
                'emotional_intensity': vote.emotional_intensity,
                'darkness': vote.darkness,
                'character_focus': vote.character_focus,
                'introspection': vote.introspection,
                'themes': vote.themes,
                'primary_themes': vote.primary_themes,
                'genre_tags': vote.genre_tags,
                'primary_genre_tag': vote.primary_genre_tag,
            }

        return Response({
            'has_voted': has_voted,
            'vote': vote_data
        })


class SurveyConfigView(APIView):
    """
    GET /api/recommendations/survey/config/
    Get survey configuration (questions, categorized themes, genre tags, popularity).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from collections import Counter

        # Calculate theme popularity (count across all votes)
        all_votes = BookDNAVote.objects.values_list('themes', flat=True)
        theme_counter = Counter()
        for themes_list in all_votes:
            if themes_list:
                theme_counter.update(themes_list)

        # Sort themes within each category by popularity
        sorted_categories = []
        for cat in THEME_CATEGORIES:
            sorted_themes = sorted(
                cat["themes"],
                key=lambda t: theme_counter.get(t["id"], 0),
                reverse=True
            )
            sorted_categories.append({
                **cat,
                "themes": sorted_themes
            })

        return Response({
            'questions': SURVEY_QUESTIONS,
            'theme_options': THEME_OPTIONS,
            'theme_categories': sorted_categories,
            'genre_tag_options': GENRE_TAG_OPTIONS,
            'theme_popularity': dict(theme_counter),
        })


class TasteProfileView(APIView):
    """
    GET /api/recommendations/taste-profile/
    Get user's taste profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_user_taste_profile(request.user)
        serializer = TasteProfileSerializer(profile)
        return Response(serializer.data)


class BookDNAView(APIView):
    """
    GET /api/recommendations/book-dna/{book_id}/
    Get DNA for a specific book (or from any edition in the same group).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        # Try to get DNA for this specific book
        dna = None
        try:
            dna = book.dna
        except BookDNA.DoesNotExist:
            pass

        # If no DNA for this book, check other editions in the same group
        if not dna and book.book_group_id:
            for edition in book.book_group.editions.exclude(id=book_id):
                try:
                    dna = edition.dna
                    break
                except BookDNA.DoesNotExist:
                    continue

        if dna:
            serializer = BookDNASerializer(dna)
            return Response(serializer.data)
        else:
            return Response({
                'detail': 'No DNA data available for this book yet.',
                'book_id': book_id
            }, status=status.HTTP_404_NOT_FOUND)
