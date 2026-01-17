from django.db import models 
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from apps.challenges.models import ReadingChallenge
from apps.challenges.serializers import (
    ReadingChallengeListSerializer,
    ReadingChallengeDetailSerializer,
    ReadingChallengeCreateSerializer,
    ReadingChallengeUpdateSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user


class ReadingChallengeViewSet(viewsets.ModelViewSet):
    """ViewSet for ReadingChallenge model"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'target_books']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReadingChallengeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReadingChallengeUpdateSerializer
        elif self.action == 'retrieve':
            return ReadingChallengeDetailSerializer
        return ReadingChallengeListSerializer
    
    def get_queryset(self):
        """Filter queryset by user and status"""
        queryset = ReadingChallenge.objects.all().prefetch_related(
            'genre_filter',
            'tag_filter'
        )
        
        # Filter by current user or specific user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        else:
            # Default to current user's challenges
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by active status
        is_active = self.request.query_params.get('active', None)
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Filter by completed
        is_completed = self.request.query_params.get('completed', None)
        if is_completed == 'true':
            queryset = queryset.filter(completed_books__gte=models.F('target_books'))
        elif is_completed == 'false':
            queryset = queryset.filter(completed_books__lt=models.F('target_books'))
        
        # Filter by year
        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(start_date__year=year)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Manually recalculate challenge progress"""
        challenge = self.get_object()
        challenge.update_progress()
        serializer = ReadingChallengeDetailSerializer(challenge)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle challenge active status"""
        challenge = self.get_object()
        challenge.is_active = not challenge.is_active
        challenge.save()
        serializer = ReadingChallengeDetailSerializer(challenge)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active challenges"""
        today = timezone.now().date()
        challenges = ReadingChallenge.objects.filter(
            user=request.user,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = ReadingChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed challenges"""
        from django.db import models
        challenges = ReadingChallenge.objects.filter(
            user=request.user
        ).filter(
            completed_books__gte=models.F('target_books')
        )
        serializer = ReadingChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress_details(self, request, pk=None):
        """Get detailed progress breakdown"""
        challenge = self.get_object()
        from apps.reading.models import UserBook
        
        # Get books that count toward this challenge
        query = UserBook.objects.filter(
            user=request.user,
            status='read',
            finished_at__gte=challenge.start_date,
            finished_at__lte=challenge.end_date
        )
        
        # Apply filters
        if challenge.genre_filter.exists():
            query = query.filter(book__genres__in=challenge.genre_filter.all())
        
        if challenge.tag_filter.exists():
            query = query.filter(book__tags__in=challenge.tag_filter.all())
        
        if challenge.min_pages:
            query = query.filter(book__pages__gte=challenge.min_pages)
        
        books = query.distinct().select_related('book').prefetch_related('book__authors')
        
        from apps.reading.serializers import UserBookListSerializer
        serializer = UserBookListSerializer(books, many=True)
        
        return Response({
            'challenge': ReadingChallengeDetailSerializer(challenge).data,
            'qualifying_books': serializer.data,
            'count': books.count(),
        })

