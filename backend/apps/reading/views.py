import csv
import json
import io
from django.http import HttpResponse
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count

from apps.reading.models import UserBook, Quote, QuoteTag, VocabularyWord
from apps.reading.models_study import StudyNote
from apps.reading.serializers import (
    UserBookListSerializer,
    UserBookDetailSerializer,
    UserBookCreateSerializer,
    QuoteListSerializer,
    QuoteDetailSerializer,
    QuoteCreateSerializer,
    QuoteUpdateSerializer,
    QuoteTagSerializer,
    VocabularyWordSerializer,
)
from apps.reading.serializers_study import (
    StudyNoteListSerializer,
    StudyNoteDetailSerializer,
    StudyNoteCreateSerializer,
    StudyNoteUpdateSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


class UserBookViewSet(viewsets.ModelViewSet):
    """ViewSet for UserBook model"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['book__title', 'book__authors__name', 'review']
    ordering_fields = ['updated_at', 'created_at', 'started_at', 'finished_at', 'rating']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserBookCreateSerializer
        elif self.action == 'retrieve':
            return UserBookDetailSerializer
        return UserBookListSerializer
    
    def get_queryset(self):
        """Filter queryset by user and status"""
        queryset = UserBook.objects.all().select_related(
            'user',
            'book',
            'book__publisher'
        ).prefetch_related(
            'book__authors',
            'book__genres',
            'quotes',
        )
        
        # Filter by current user or specific user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        else:
            # Default to current user's books
            queryset = queryset.filter(user=self.request.user)

        # Filter by owned — when viewing physical shelf, include replaced editions
        # (user still physically owns the old edition even if they switched to a new one for reading)
        is_owned = self.request.query_params.get('owned', None)
        if is_owned == 'true':
            queryset = queryset.filter(is_owned=True)
        else:
            # Only return ACTIVE UserBooks (not replaced by another edition) for non-shelf views
            queryset = queryset.filter(replaced_by__isnull=True)

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by favorite
        is_favorite = self.request.query_params.get('favorite', None)
        if is_favorite == 'true':
            queryset = queryset.filter(is_favorite=True)

        # Filter by rating
        rating = self.request.query_params.get('rating', None)
        if rating:
            queryset = queryset.filter(rating=rating)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Override create to handle duplicates gracefully.
        If user already has this book, update ownership fields and return it.
        """
        book_id = request.data.get('book')

        # Check if user already has this book
        existing = UserBook.objects.filter(
            user=request.user,
            book_id=book_id
        ).first()

        if existing:
            # Update ownership/wishlist fields if provided in the request
            updated = False
            if 'is_owned' in request.data and request.data['is_owned'] != existing.is_owned:
                existing.is_owned = request.data['is_owned']
                updated = True
            if 'is_wishlisted' in request.data and request.data['is_wishlisted'] != existing.is_wishlisted:
                existing.is_wishlisted = request.data['is_wishlisted']
                updated = True
            if updated:
                existing.save(update_fields=['is_owned', 'is_wishlisted'])
            serializer = self.get_serializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create new UserBook if it doesn't exist
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Handle status changes and automatically set dates:
        - Set started_at when status changes to 'currently_reading'
        - Set finished_at when status changes to 'read'
        """
        from django.utils import timezone

        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)

        # Auto-set started_at when beginning to read
        if new_status == 'currently_reading' and old_status != 'currently_reading':
            if not instance.started_at:
                serializer.validated_data['started_at'] = timezone.now().date()

        # Auto-set finished_at when marking as read
        if new_status == 'read' and old_status != 'read':
            if not instance.finished_at:
                serializer.validated_data['finished_at'] = timezone.now().date()

        serializer.save()

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update reading progress"""
        user_book = self.get_object()
        current_page = request.data.get('current_page')
        
        if current_page is None:
            return Response(
                {'error': 'current_page is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_book.current_page = current_page
        user_book.save()
        
        serializer = UserBookDetailSerializer(user_book)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_owned(self, request, pk=None):
        """Toggle ownership status of a book"""
        user_book = self.get_object()
        user_book.is_owned = not user_book.is_owned
        user_book.save(update_fields=['is_owned'])
        serializer = UserBookListSerializer(user_book)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_wishlisted(self, request, pk=None):
        """Toggle wishlist status of a book"""
        user_book = self.get_object()
        user_book.is_wishlisted = not user_book.is_wishlisted
        # If wishlisting, remove owned flag (and vice versa)
        if user_book.is_wishlisted and user_book.is_owned:
            user_book.is_owned = False
        user_book.save(update_fields=['is_wishlisted', 'is_owned'])
        serializer = UserBookListSerializer(user_book)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def wishlist(self, request):
        """Get a user's wishlist (wishlisted books). Accessible by other users."""
        user_id = request.query_params.get('user', request.user.id)
        wishlisted = UserBook.objects.filter(
            user_id=user_id,
            is_wishlisted=True,
        ).select_related(
            'book', 'book__publisher'
        ).prefetch_related('book__authors', 'book__genres')
        serializer = UserBookListSerializer(wishlisted, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_toggle_owned(self, request):
        """Set is_owned for multiple books at once"""
        book_ids = request.data.get('ids', [])
        is_owned = request.data.get('is_owned', True)
        updated = UserBook.objects.filter(
            user=request.user, id__in=book_ids
        ).update(is_owned=is_owned)
        return Response({'updated': updated})

    @action(detail=False, methods=['get'])
    def book_knowledge(self, request):
        """Aggregated knowledge for a specific book: quotes, study notes, vocabulary, journal entries"""
        book_id = request.query_params.get('book')
        if not book_id:
            return Response({'error': 'book parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.codex.models import JournalEntry
        from apps.codex.serializers import JournalEntrySerializer

        quotes = Quote.objects.filter(user=request.user, book_id=book_id).select_related('book').prefetch_related('tags')
        study_notes = StudyNote.objects.filter(user=request.user, book_id=book_id).prefetch_related('tags')
        vocabulary = VocabularyWord.objects.filter(user=request.user, book_id=book_id)
        journal_entries = JournalEntry.objects.filter(user=request.user, book_id=book_id)

        return Response({
            'quotes': {
                'count': quotes.count(),
                'recent': QuoteListSerializer(quotes[:5], many=True).data,
            },
            'study_notes': {
                'count': study_notes.count(),
                'recent': StudyNoteListSerializer(study_notes[:5], many=True).data,
            },
            'vocabulary': {
                'count': vocabulary.count(),
                'recent': VocabularyWordSerializer(vocabulary[:5], many=True).data,
            },
            'journal_entries': {
                'count': journal_entries.count(),
                'recent': JournalEntrySerializer(journal_entries[:5], many=True).data,
            },
        })

    @action(detail=True, methods=['post'])
    def mark_finished(self, request, pk=None):
        """Mark book as finished"""
        user_book = self.get_object()
        from datetime import date
        
        user_book.status = 'read'
        user_book.finished_at = request.data.get('finished_at', date.today())
        user_book.save()
        
        serializer = UserBookDetailSerializer(user_book)
        return Response(serializer.data)


class QuoteTagViewSet(viewsets.ModelViewSet):
    """ViewSet for QuoteTag model"""
    serializer_class = QuoteTagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter to current user's tags"""
        return QuoteTag.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create tag or return existing one if duplicate"""
        tag_name = request.data.get('name', '').strip()

        # Check if tag already exists for this user
        existing_tag = QuoteTag.objects.filter(
            user=request.user,
            name__iexact=tag_name
        ).first()

        if existing_tag:
            # Return existing tag instead of creating duplicate
            serializer = self.get_serializer(existing_tag)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Create new tag if doesn't exist
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)


class QuoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Quote model"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text', 'note', 'book__title']
    ordering_fields = ['created_at', 'page_number']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return QuoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return QuoteUpdateSerializer
        elif self.action == 'retrieve':
            return QuoteDetailSerializer
        return QuoteListSerializer
    
    def get_queryset(self):
        """Filter queryset by user and various parameters"""
        queryset = Quote.objects.all().select_related(
            'user',
            'book',
            'user_book'
        ).prefetch_related('tags')
        
        # Filter by current user or specific user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        else:
            # Default to current user's quotes
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by book
        book_id = self.request.query_params.get('book', None)
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        # Filter by tag
        tag_id = self.request.query_params.get('tag', None)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # Filter by favorite
        is_favorite = self.request.query_params.get('favorite', None)
        if is_favorite == 'true':
            queryset = queryset.filter(is_favorite=True)
        
        # Filter by public
        is_public = self.request.query_params.get('public', None)
        if is_public == 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        """Get current user's favorite quotes"""
        quotes = Quote.objects.filter(
            user=request.user,
            is_favorite=True
        ).select_related('book').prefetch_related('tags')
        
        serializer = QuoteListSerializer(quotes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """Get quotes grouped by tags"""
        tag_id = request.query_params.get('tag_id')
        if not tag_id:
            return Response(
                {'error': 'tag_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quotes = Quote.objects.filter(
            user=request.user,
            tags__id=tag_id
        ).select_related('book').prefetch_related('tags')
        
        serializer = QuoteListSerializer(quotes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_semantic(self, request):
        """
        Semantic search through quotes.
        TODO: Implement with AI embeddings later
        For now, just basic text search
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'q parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quotes = Quote.objects.filter(
            user=request.user
        ).filter(
            Q(text__icontains=query) | Q(note__icontains=query)
        ).select_related('book').prefetch_related('tags')

        serializer = QuoteListSerializer(quotes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export all quotes as JSON or CSV"""
        quotes = self.get_queryset()
        fmt = request.query_params.get('format', 'json')

        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Text', 'Book Title', 'Book Author', 'Page', 'Chapter', 'Note', 'Tags', 'Favorite', 'Date'])
            for q in quotes:
                writer.writerow([
                    q.text,
                    q.book_title or (q.book.title if q.book else ''),
                    q.book_author or '',
                    q.page_number or '',
                    q.chapter or '',
                    q.note or '',
                    ', '.join(t.name for t in q.tags.all()),
                    'Yes' if q.is_favorite else 'No',
                    q.created_at.strftime('%Y-%m-%d') if q.created_at else '',
                ])
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="quotes.csv"'
            return response
        else:
            serializer = QuoteListSerializer(quotes, many=True)
            data = json.dumps(serializer.data, indent=2, default=str, ensure_ascii=False)
            response = HttpResponse(data, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="quotes.json"'
            return response


class StudyNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyNote model - deep study and scholarship"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'reference', 'chapter']
    ordering_fields = ['created_at', 'reference', 'note_type']
    ordering = ['reference', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return StudyNoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudyNoteUpdateSerializer
        elif self.action == 'retrieve':
            return StudyNoteDetailSerializer
        return StudyNoteListSerializer

    def get_queryset(self):
        """Filter queryset by user and parameters"""
        queryset = StudyNote.objects.all().select_related(
            'user',
            'book',
            'user_book'
        ).prefetch_related('tags')

        # Filter by current user
        queryset = queryset.filter(user=self.request.user)

        # Filter by book
        book_id = self.request.query_params.get('book', None)
        if book_id:
            queryset = queryset.filter(book_id=book_id)

        # Filter by note type
        note_type = self.request.query_params.get('type', None)
        if note_type:
            queryset = queryset.filter(note_type=note_type)

        # Filter by reference
        reference = self.request.query_params.get('reference', None)
        if reference:
            queryset = queryset.filter(reference=reference)

        # Filter by tag
        tag_id = self.request.query_params.get('tag', None)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create note and return full data using list serializer"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=request.user)
        output = StudyNoteListSerializer(instance).data
        return Response(output, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update note and return full data using list serializer"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output = StudyNoteListSerializer(instance).data
        return Response(output)

    @action(detail=False, methods=['get'])
    def references(self, request):
        """Get list of all unique references for a book"""
        book_id = request.query_params.get('book')
        if not book_id:
            return Response(
                {'error': 'book parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        references = StudyNote.objects.filter(
            user=request.user,
            book_id=book_id
        ).values('reference').annotate(
            count=Count('id')
        ).order_by('reference')

        return Response(references)

    @action(detail=False, methods=['get'])
    def books_with_notes(self, request):
        """Get book IDs that have study notes, sorted by count"""
        books = StudyNote.objects.filter(
            user=request.user
        ).values('book_id').annotate(
            count=Count('id')
        ).order_by('-count')
        return Response(list(books))

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export study notes as JSON (optionally filtered by book)"""
        notes = self.get_queryset()
        serializer = StudyNoteListSerializer(notes, many=True)
        data = json.dumps(serializer.data, indent=2, default=str, ensure_ascii=False)
        response = HttpResponse(data, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="study_notes.json"'
        return response

    @action(detail=True, methods=['post'])
    def promote_to_quote(self, request, pk=None):
        """Promote a study note to a main quote"""
        study_note = self.get_object()

        if study_note.is_promoted_to_quote:
            return Response(
                {'error': 'Note already promoted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a Quote from the study note
        quote = Quote.objects.create(
            user=request.user,
            book=study_note.book,
            user_book=study_note.user_book,
            book_title=study_note.book.title if study_note.book else '',
            book_author=', '.join(a.name for a in study_note.book.authors.all()) if study_note.book else '',
            text=study_note.content,
            page_number=study_note.page_number,
            chapter=study_note.chapter,
            is_public=study_note.is_public
        )

        # Copy tags
        quote.tags.set(study_note.tags.all())

        # Mark as promoted
        study_note.is_promoted_to_quote = True
        study_note.promoted_quote = quote
        study_note.save()

        return Response({
            'message': 'Note promoted to quote',
            'quote_id': quote.id
        })


class VocabularyWordViewSet(viewsets.ModelViewSet):
    """ViewSet for vocabulary words"""
    serializer_class = VocabularyWordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['word', 'definition', 'context']
    ordering_fields = ['word', 'created_at', 'mastery', 'review_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter vocabulary words by user"""
        queryset = VocabularyWord.objects.filter(user=self.request.user)

        # Filter by mastery level
        mastery = self.request.query_params.get('mastery', None)
        if mastery:
            queryset = queryset.filter(mastery=mastery)

        # Filter by favorite
        favorite = self.request.query_params.get('favorite', None)
        if favorite and favorite.lower() == 'true':
            queryset = queryset.filter(is_favorite=True)

        # Filter by book
        book_id = self.request.query_params.get('book', None)
        if book_id:
            queryset = queryset.filter(book_id=book_id)

        return queryset

    def perform_create(self, serializer):
        """Set user when creating vocabulary word"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_mastery(self, request, pk=None):
        """Update mastery level and increment review count"""
        word = self.get_object()
        mastery = request.data.get('mastery')

        if mastery not in ['new', 'learning', 'mastered']:
            return Response(
                {'error': 'Invalid mastery level'},
                status=status.HTTP_400_BAD_REQUEST
            )

        word.mastery = mastery
        word.review_count += 1
        from django.utils import timezone
        word.last_reviewed_at = timezone.now()
        word.save()

        return Response(VocabularyWordSerializer(word).data)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status"""
        word = self.get_object()
        word.is_favorite = not word.is_favorite
        word.save()
        return Response(VocabularyWordSerializer(word).data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export vocabulary as JSON, CSV, or Anki-compatible format"""
        words = self.get_queryset()
        fmt = request.query_params.get('format', 'json')

        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Word', 'Definition', 'Context', 'Book', 'Author', 'Page', 'Mastery', 'Date'])
            for w in words:
                writer.writerow([
                    w.word,
                    w.definition or '',
                    w.context or '',
                    w.book_title or (w.book.title if w.book else ''),
                    w.book_author or '',
                    w.page_number or '',
                    w.mastery,
                    w.created_at.strftime('%Y-%m-%d') if w.created_at else '',
                ])
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="vocabulary.csv"'
            return response
        elif fmt == 'anki':
            # Tab-separated: front\tback (Anki import format)
            lines = []
            for w in words:
                front = w.word
                back_parts = []
                if w.definition:
                    back_parts.append(w.definition)
                if w.context:
                    back_parts.append(f'Context: "{w.context}"')
                source = w.book_title or (w.book.title if w.book else '')
                if source:
                    back_parts.append(f'Source: {source}')
                back = '<br>'.join(back_parts)
                lines.append(f'{front}\t{back}')
            content = '\n'.join(lines)
            response = HttpResponse(content, content_type='text/tab-separated-values; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="vocabulary_anki.txt"'
            return response
        else:
            serializer = VocabularyWordSerializer(words, many=True)
            data = json.dumps(serializer.data, indent=2, default=str, ensure_ascii=False)
            response = HttpResponse(data, content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="vocabulary.json"'
            return response

