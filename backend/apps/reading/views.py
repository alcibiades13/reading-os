from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count

from apps.reading.models import UserBook, Quote, QuoteTag
from apps.reading.serializers import (
    UserBookListSerializer,
    UserBookDetailSerializer,
    UserBookCreateSerializer,
    QuoteListSerializer,
    QuoteDetailSerializer,
    QuoteCreateSerializer,
    QuoteTagSerializer,
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

    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Handle status changes and automatically set dates:
        - Set started_at when status changes to 'currently_reading'
        - Set finished_at when status changes to 'read'
        """
        from datetime import date

        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)

        # Auto-set started_at when beginning to read
        if new_status == 'currently_reading' and old_status != 'currently_reading':
            if not instance.started_at:
                serializer.validated_data['started_at'] = date.today()

        # Auto-set finished_at when marking as read
        if new_status == 'read' and old_status != 'read':
            if not instance.finished_at:
                serializer.validated_data['finished_at'] = date.today()

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
