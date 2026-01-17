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
        If user already has this book, return the existing UserBook.
        """
        book_id = request.data.get('book')

        # Check if user already has this book
        existing = UserBook.objects.filter(
            user=request.user,
            book_id=book_id
        ).first()

        if existing:
            # Return existing UserBook instead of creating duplicate
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

    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)

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

