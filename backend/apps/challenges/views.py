from django.db import models 
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from apps.challenges.models import ReadingChallenge, ReadingSchedule, ReadingScheduleSection
from apps.challenges.serializers import (
    ReadingChallengeListSerializer,
    ReadingChallengeDetailSerializer,
    ReadingChallengeCreateSerializer,
    ReadingChallengeUpdateSerializer,
    ReadingScheduleSerializer,
    ReadingScheduleSectionSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user


class ReadingChallengeViewSet(viewsets.ModelViewSet):
    """ViewSet for ReadingChallenge model"""
    pagination_class = None  # User-scoped: small dataset
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
        if user_id and str(user_id) != str(self.request.user.id):
            # Viewing another user's challenges - only return public ones
            queryset = queryset.filter(user_id=user_id, is_public=True)
        elif user_id:
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
        """Get detailed progress breakdown with list of qualifying items."""
        challenge = self.get_object()

        if challenge.challenge_type == challenge.TYPE_VOCABULARY:
            from apps.reading.models import VocabularyWord
            words = VocabularyWord.objects.filter(
                user=request.user,
                created_at__date__gte=challenge.start_date,
                created_at__date__lte=challenge.end_date,
            ).order_by('created_at').select_related('book')

            items = [
                {
                    'id': w.id,
                    'word': w.word,
                    'definition': w.definition,
                    'mastery': w.mastery,
                    'book_title': w.book.title if w.book else w.book_title,
                    'created_at': w.created_at.date(),
                }
                for w in words
            ]
            return Response({
                'challenge': ReadingChallengeDetailSerializer(challenge).data,
                'qualifying_items': items,
                'item_type': 'vocabulary',
                'count': len(items),
            })

        # Default: books
        from apps.reading.models import BookReadLog
        logs = BookReadLog.objects.filter(
            user_book__user=request.user,
            finished_at__gte=challenge.start_date,
            finished_at__lte=challenge.end_date,
        ).select_related('user_book__book').prefetch_related('user_book__book__authors')

        if challenge.genre_filter.exists():
            logs = logs.filter(user_book__book__genres__in=challenge.genre_filter.all())
        if challenge.tag_filter.exists():
            logs = logs.filter(user_book__book__tags__in=challenge.tag_filter.all())
        if challenge.min_pages:
            logs = logs.filter(user_book__book__pages__gte=challenge.min_pages)

        seen = set()
        items = []
        for log in logs:
            book = log.user_book.book
            if book.id not in seen:
                seen.add(book.id)
                items.append({
                    'id': book.id,
                    'title': book.title,
                    'cover_image': book.cover_image,
                    'authors': [a.name for a in book.authors.all()],
                    'pages': book.pages,
                    'finished_at': log.finished_at,
                    'slug': book.slug,
                })

        return Response({
            'challenge': ReadingChallengeDetailSerializer(challenge).data,
            'qualifying_items': items,
            'item_type': 'books',
            'count': len(items),
        })


class ReadingScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ReadingSchedule.objects.filter(
            user=self.request.user
        ).prefetch_related('sections')

    def perform_create(self, serializer):
        schedule = serializer.save(user=self.request.user)
        # Create 3 default sections
        defaults = ['January', 'February', 'March']
        for i, name in enumerate(defaults):
            ReadingScheduleSection.objects.create(
                schedule=schedule, title=name, order=i
            )

    @action(detail=True, methods=['post'])
    def add_section(self, request, pk=None):
        schedule = self.get_object()
        title = request.data.get('title', 'New Section')
        order = schedule.sections.count()
        section = ReadingScheduleSection.objects.create(
            schedule=schedule, title=title, order=order
        )
        return Response(ReadingScheduleSectionSerializer(section).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='sections/(?P<section_id>[0-9]+)')
    def update_section(self, request, pk=None, section_id=None):
        schedule = self.get_object()
        section = ReadingScheduleSection.objects.get(id=section_id, schedule=schedule)
        for field in ('title', 'book_ids', 'order'):
            if field in request.data:
                setattr(section, field, request.data[field])
        section.save()
        return Response(ReadingScheduleSectionSerializer(section).data)

    @action(detail=True, methods=['delete'], url_path='sections/(?P<section_id>[0-9]+)/delete')
    def delete_section(self, request, pk=None, section_id=None):
        schedule = self.get_object()
        ReadingScheduleSection.objects.filter(id=section_id, schedule=schedule).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

