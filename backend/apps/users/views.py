import io
import json
import logging
import zipfile
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, Count, Sum, F
from django.db.models.functions import TruncMonth, TruncDate

from apps.users.models import User, UserProfile, AccountToken
from apps.users.serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)


class AuthRateThrottle(AnonRateThrottle):
    rate = '5/minute'


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Handles user CRUD operations, registration, and profile management.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter queryset based on permissions"""
        queryset = User.objects.all()
        
        # Non-authenticated users see only public profiles
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(profile__is_public=True)
        
        return queryset.select_related('profile').prefetch_related(
            'user_books',
            'quotes',
            'reading_lists',
        )
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_throttles(self):
        if self.action in ['create', 'login', 'forgot_password']:
            return [AuthRateThrottle()]
        return super().get_throttles()
    
    def perform_create(self, serializer):
        """Create user and return tokens"""
        user = serializer.save()
        return user
    
    def create(self, request, *args, **kwargs):
        """Register new user and return JWT tokens"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        headers = self.get_success_headers(serializer.data)
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny],
            throttle_classes=[AuthRateThrottle])
    def login(self, request):
        """
        Login endpoint.
        POST /api/users/login/
        Body: {"email": "...", "password": "..."}
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get current user profile.
        GET /api/users/me/
        """
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Update current user profile.
        PUT/PATCH /api/users/update_profile/
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(request.user, context={'request': request}).data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get user reading statistics.
        GET /api/users/{id}/stats/
        """
        user = self.get_object()
        
        # Check if user profile is public or if requesting own profile
        if not user.profile.is_public and user != request.user:
            return Response(
                {'error': 'This profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.reading.models import UserBook
        from django.db.models import Count, Avg
        
        # Calculate statistics
        user_books = UserBook.objects.filter(user=user)
        
        stats = {
            'total_books': user_books.count(),
            'books_read': user_books.filter(status='read').count(),
            'currently_reading': user_books.filter(status='currently_reading').count(),
            'want_to_read': user_books.filter(status='want_to_read').count(),
            'total_quotes': user.quotes.count(),
            'average_rating': user_books.filter(rating__isnull=False).aggregate(
                avg=Avg('rating')
            )['avg'],
            'total_pages_read': sum([
                ub.book.pages for ub in user_books.filter(
                    status='read',
                    book__pages__isnull=False
                )
            ]),
            'favorite_books_count': user_books.filter(is_favorite=True).count(),
            'reading_lists_count': user.reading_lists.count(),
            'active_challenges_count': user.challenges.filter(is_active=True).count(),
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search users by name or email.
        GET /api/users/search/?q=query
        """
        query = request.query_params.get('q', '').strip()

        if not query or len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search in first_name, last_name, email (no username field in this model)
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

        # Exclude current user if authenticated
        if request.user.is_authenticated:
            users = users.exclude(id=request.user.id)

        # Filter by public profiles if not authenticated
        if not request.user.is_authenticated:
            users = users.filter(profile__is_public=True)

        # Limit results
        users = users[:20]

        # Add basic stats to each user
        from apps.reading.models import UserBook
        from apps.social.models import Friendship

        users_data = []
        for user in users:
            user_serialized = UserSerializer(user, context={'request': request}).data

            # Add stats (with safe defaults)
            try:
                user_serialized['books_read_count'] = UserBook.objects.filter(user=user, status='read').count()
            except:
                user_serialized['books_read_count'] = 0

            try:
                user_serialized['quotes_count'] = user.quotes.count()
            except:
                user_serialized['quotes_count'] = 0

            try:
                user_serialized['followers_count'] = Friendship.objects.filter(to_user=user, status='accepted').count()
            except:
                user_serialized['followers_count'] = 0

            try:
                user_serialized['following_count'] = Friendship.objects.filter(from_user=user, status='accepted').count()
            except:
                user_serialized['following_count'] = 0

            # Add following status if authenticated
            if request.user.is_authenticated:
                try:
                    user_serialized['is_following'] = Friendship.objects.filter(
                        from_user=request.user,
                        to_user=user,
                        status='accepted'
                    ).exists()
                except:
                    user_serialized['is_following'] = False
            else:
                user_serialized['is_following'] = False

            users_data.append(user_serialized)

        return Response(users_data)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """
        Get user profile with social info.
        GET /api/users/{id}/profile/
        """
        user = self.get_object()

        # Check if profile is public or if requesting own profile
        if not user.profile.is_public and user != request.user:
            return Response(
                {'error': 'This profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.social.models import Friendship

        # Get friendship status
        is_following = False
        is_follower = False
        friendship_id = None

        if request.user.is_authenticated and user != request.user:
            # Check if current user follows this user
            following_friendship = Friendship.objects.filter(
                from_user=request.user,
                to_user=user,
                status='accepted'
            ).first()

            if following_friendship:
                is_following = True
                friendship_id = following_friendship.id

            # Check if this user follows current user
            is_follower = Friendship.objects.filter(
                from_user=user,
                to_user=request.user,
                status='accepted'
            ).exists()

        # Count followers and following
        followers_count = Friendship.objects.filter(
            to_user=user,
            status='accepted'
        ).count()

        following_count = Friendship.objects.filter(
            from_user=user,
            status='accepted'
        ).count()

        # Get books and quotes count
        from apps.reading.models import UserBook

        books_read_count = UserBook.objects.filter(
            user=user,
            status='read'
        ).count()

        quotes_count = user.quotes.count()

        # Get top genres
        from apps.books.models import Genre
        from django.db.models import Count

        top_genres = Genre.objects.filter(
            books__user_books__user=user,
            books__user_books__status='read'
        ).annotate(
            count=Count('books')
        ).order_by('-count').values_list('name', flat=True)[:5]

        # Compute shared books and match score (only when viewing someone else's profile)
        shared_books_data = []
        shared_books_count = 0
        match_score = 0
        if request.user.is_authenticated and user != request.user:
            # Compare at book_group level: different editions of the same work count as a match
            current_user_books = UserBook.objects.filter(
                user=request.user,
                replaced_by__isnull=True
            ).select_related('book')
            current_user_group_ids = set(
                current_user_books.filter(
                    book__book_group__isnull=False
                ).values_list('book__book_group_id', flat=True)
            )
            current_user_solo_book_ids = set(
                current_user_books.filter(
                    book__book_group__isnull=True
                ).values_list('book_id', flat=True)
            )
            shared_user_books = UserBook.objects.filter(
                user=user,
                replaced_by__isnull=True,
            ).filter(
                Q(book__book_group_id__in=current_user_group_ids) |
                Q(book_id__in=current_user_solo_book_ids, book__book_group__isnull=True)
            ).select_related('book').prefetch_related('book__authors')

            shared_books_count = shared_user_books.count()

            from apps.books.serializers import BookListSerializer
            shared_books_data = [
                {
                    'id': ub.id,
                    'book': BookListSerializer(ub.book).data,
                    'status': ub.status,
                    'rating': str(ub.rating) if ub.rating else None,
                }
                for ub in shared_user_books
            ]

            # Compute match score based on shared books and genres
            current_user_genres = set(
                Genre.objects.filter(
                    books__user_books__user=request.user,
                    books__user_books__status='read'
                ).values_list('name', flat=True)
            )
            other_user_genres = set(top_genres)
            shared_genres_count = len(current_user_genres & other_user_genres)

            # Total books for both users
            current_total = current_user_books.count()
            other_total = UserBook.objects.filter(
                user=user, replaced_by__isnull=True
            ).count()
            min_total = min(current_total, other_total) or 1

            # Match score with diminishing returns on shared book count
            # Books score (0-60): first 10 books = 2pts each, then 0.8pts each
            if shared_books_count <= 10:
                books_score = shared_books_count * 2
            else:
                books_score = 20 + (shared_books_count - 10) * 0.8
            books_score = min(books_score, 60)

            # Genres score (0-30): 8pts per shared genre
            genres_score = min(shared_genres_count * 8, 30)

            # Overlap ratio bonus (0-10): how much of the smaller library overlaps
            overlap_ratio = shared_books_count / min_total
            overlap_bonus = min(overlap_ratio * 10, 10)

            match_score = round(min(books_score + genres_score + overlap_bonus, 100))

        # Get user's reading DNA
        from apps.recommendations.aggregation import get_user_taste_profile
        reading_dna = get_user_taste_profile(user)

        # Serialize user data
        user_data = UserDetailSerializer(user, context={'request': request}).data
        user_data.update({
            'is_following': is_following,
            'is_follower': is_follower,
            'friendship_id': friendship_id,
            'followers_count': followers_count,
            'following_count': following_count,
            'books_read_count': books_read_count,
            'quotes_count': quotes_count,
            'top_genres': list(top_genres),
            'shared_books': shared_books_data,
            'shared_books_count': shared_books_count,
            'match_score': match_score,
            'reading_dna': reading_dna,
        })

        return Response(user_data)

    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """
        Get user's books with pagination.
        GET /api/users/{id}/books/?status=read&page=1&page_size=20
        """
        user = self.get_object()

        # Check if profile is public or if requesting own profile
        if not user.profile.is_public and user != request.user:
            return Response(
                {'error': 'This profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.reading.models import UserBook
        from apps.reading.serializers import UserBookListSerializer
        from django.core.paginator import Paginator

        # Get user's books (exclude replaced editions)
        queryset = UserBook.objects.filter(
            user=user,
            replaced_by__isnull=True
        ).select_related(
            'book'
        ).prefetch_related(
            'book__authors',
            'book__genres'
        )

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Order by date added
        queryset = queryset.order_by('-created_at')

        # Paginate - default 20 per page
        page_size = int(request.query_params.get('page_size', 20))
        page_number = int(request.query_params.get('page', 1))

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)

        serializer = UserBookListSerializer(page_obj, many=True)

        return Response({
            'count': paginator.count,
            'next': page_obj.has_next() and page_obj.next_page_number() or None,
            'previous': page_obj.has_previous() and page_obj.previous_page_number() or None,
            'results': serializer.data
        })

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """
        Get user's followers.
        GET /api/users/{id}/followers/
        """
        user = self.get_object()

        # Check if profile is public or if requesting own profile
        if not user.profile.is_public and user != request.user:
            return Response(
                {'error': 'This profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.social.models import Friendship

        # Get users who follow this user
        follower_friendships = Friendship.objects.filter(
            to_user=user,
            status='accepted'
        ).select_related('from_user')

        followers_data = []
        for friendship in follower_friendships:
            follower = friendship.from_user
            follower_serialized = UserSerializer(follower, context={'request': request}).data

            # Add stats
            from apps.reading.models import UserBook
            follower_serialized['books_read_count'] = UserBook.objects.filter(user=follower, status='read').count()
            follower_serialized['quotes_count'] = follower.quotes.count()
            follower_serialized['followers_count'] = Friendship.objects.filter(to_user=follower, status='accepted').count()
            follower_serialized['following_count'] = Friendship.objects.filter(from_user=follower, status='accepted').count()

            # Add following status if authenticated
            if request.user.is_authenticated:
                follower_serialized['is_following'] = Friendship.objects.filter(
                    from_user=request.user,
                    to_user=follower,
                    status='accepted'
                ).exists()
                follower_serialized['is_follower'] = Friendship.objects.filter(
                    from_user=follower,
                    to_user=request.user,
                    status='accepted'
                ).exists()
            else:
                follower_serialized['is_following'] = False
                follower_serialized['is_follower'] = False

            followers_data.append(follower_serialized)

        return Response(followers_data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """
        Get users that this user follows.
        GET /api/users/{id}/following/
        """
        user = self.get_object()

        # Check if profile is public or if requesting own profile
        if not user.profile.is_public and user != request.user:
            return Response(
                {'error': 'This profile is private'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.social.models import Friendship

        # Get users that this user follows
        following_friendships = Friendship.objects.filter(
            from_user=user,
            status='accepted'
        ).select_related('to_user')

        following_data = []
        for friendship in following_friendships:
            followed_user = friendship.to_user
            followed_serialized = UserSerializer(followed_user, context={'request': request}).data

            # Add stats
            from apps.reading.models import UserBook
            followed_serialized['books_read_count'] = UserBook.objects.filter(user=followed_user, status='read').count()
            followed_serialized['quotes_count'] = followed_user.quotes.count()
            followed_serialized['followers_count'] = Friendship.objects.filter(to_user=followed_user, status='accepted').count()
            followed_serialized['following_count'] = Friendship.objects.filter(from_user=followed_user, status='accepted').count()

            # Add following status if authenticated
            if request.user.is_authenticated:
                followed_serialized['is_following'] = Friendship.objects.filter(
                    from_user=request.user,
                    to_user=followed_user,
                    status='accepted'
                ).exists()
                followed_serialized['is_follower'] = Friendship.objects.filter(
                    from_user=followed_user,
                    to_user=request.user,
                    status='accepted'
                ).exists()
            else:
                followed_serialized['is_following'] = False
                followed_serialized['is_follower'] = False

            following_data.append(followed_serialized)

        return Response(following_data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def consistency(self, request):
        """
        Get 28-day activity heatmap data with streak count.
        GET /api/users/consistency/
        """
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        from apps.reading.models import Quote, VocabularyWord
        from apps.reading.models_study import StudyNote
        from apps.codex.models import JournalEntry, Chapter
        from apps.social.models import TopicMessage, FeedItem

        user = request.user
        today = timezone.now().date()
        start_date = today - timedelta(days=27)

        def count_by_day(qs, date_field='created_at'):
            return dict(
                qs.filter(**{f'{date_field}__date__gte': start_date})
                .annotate(date=TruncDate(date_field))
                .values('date')
                .annotate(count=Count('id'))
                .values_list('date', 'count')
            )

        def distinct_days(qs, date_field='created_at'):
            return set(
                qs.filter(**{f'{date_field}__date__gte': start_date})
                .annotate(date=TruncDate(date_field))
                .values_list('date', flat=True)
                .distinct()
            )

        quotes_by_day = count_by_day(Quote.objects.filter(user=user))
        study_notes_by_day = count_by_day(StudyNote.objects.filter(user=user))
        vocabulary_by_day = count_by_day(VocabularyWord.objects.filter(user=user))
        journal_by_day = count_by_day(JournalEntry.objects.filter(user=user))
        discussions_by_day = count_by_day(TopicMessage.objects.filter(author=user))
        reading_days = distinct_days(
            FeedItem.objects.filter(actor=user, feed_type='progress_update')
        )
        writing_days = distinct_days(
            Chapter.objects.filter(manuscript__user=user), date_field='updated_at'
        )

        days = []
        for i in range(28):
            day = start_date + timedelta(days=i)
            q = quotes_by_day.get(day, 0)
            sn = study_notes_by_day.get(day, 0)
            v = vocabulary_by_day.get(day, 0)
            r = day in reading_days
            j = journal_by_day.get(day, 0)
            w = day in writing_days
            d = discussions_by_day.get(day, 0)
            total = q + sn + v + (1 if r else 0) + j + (1 if w else 0) + d
            days.append({
                'date': day.isoformat(),
                'total': total,
                'quotes': q,
                'study_notes': sn,
                'vocabulary': v,
                'reading': r,
                'journal': j,
                'writing': w,
                'discussions': d,
            })

        streak = 0
        for day_data in reversed(days):
            if day_data['total'] > 0:
                streak += 1
            else:
                break

        return Response({'streak': streak, 'days': days})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated],
            url_path='reading-stats')
    def reading_stats(self, request):
        """
        Comprehensive reading statistics dashboard data.
        GET /api/users/reading-stats/?year=2025
        """
        from apps.reading.models import UserBook, Quote, VocabularyWord
        from apps.books.models import Genre, Author

        user = request.user
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        year_start = timezone.datetime(year, 1, 1).date()
        year_end = timezone.datetime(year, 12, 31).date()

        # Base querysets
        all_user_books = UserBook.objects.filter(user=user, replaced_by__isnull=True)
        read_books = all_user_books.filter(status='read')
        year_books = read_books.filter(finished_at__gte=year_start, finished_at__lte=year_end)
        all_quotes = Quote.objects.filter(user=user)
        year_quotes = all_quotes.filter(created_at__year=year)
        all_vocab = VocabularyWord.objects.filter(user=user)
        year_vocab = all_vocab.filter(created_at__year=year)

        # ===== OVERVIEW =====
        rated_books = list(read_books.filter(rating__isnull=False).values_list('rating', flat=True))
        avg_rating = round(float(sum(rated_books)) / len(rated_books), 1) if rated_books else None

        pages_read = read_books.filter(
            book__pages__isnull=False, finished_at__gte=year_start, finished_at__lte=year_end
        ).aggregate(total=Sum('book__pages'))['total'] or 0

        # Streak (reuse consistency logic concept)
        today = now.date()
        streak = 0
        for i in range(365):
            day = today - timedelta(days=i)
            has_activity = (
                all_quotes.filter(created_at__date=day).exists() or
                all_vocab.filter(created_at__date=day).exists() or
                read_books.filter(finished_at=day).exists()
            )
            if has_activity:
                streak += 1
            else:
                break

        overview = {
            'books_read': year_books.count(),
            'total_books_read': read_books.count(),
            'pages_read': pages_read,
            'total_quotes': year_quotes.count(),
            'words_learned': year_vocab.count(),
            'avg_rating': avg_rating,
            'current_streak': streak,
        }

        # ===== MONTHLY BREAKDOWN =====
        monthly_raw = (
            year_books
            .filter(finished_at__isnull=False)
            .annotate(month=TruncMonth('finished_at'))
            .values('month')
            .annotate(books=Count('id'))
            .order_by('month')
        )
        monthly_pages_raw = (
            year_books
            .filter(finished_at__isnull=False, book__pages__isnull=False)
            .annotate(month=TruncMonth('finished_at'))
            .values('month')
            .annotate(pages=Sum('book__pages'))
            .order_by('month')
        )
        monthly_map = {m['month'].month: m['books'] for m in monthly_raw}
        pages_map = {m['month'].month: m['pages'] for m in monthly_pages_raw}
        monthly = []
        for m in range(1, 13):
            monthly.append({
                'month': m,
                'books': monthly_map.get(m, 0),
                'pages': pages_map.get(m, 0),
            })

        # ===== GENRES =====
        genre_counts = (
            Genre.objects.filter(
                books__user_books__user=user,
                books__user_books__status='read',
                books__user_books__replaced_by__isnull=True,
                books__user_books__finished_at__gte=year_start,
                books__user_books__finished_at__lte=year_end,
            )
            .annotate(count=Count('books', distinct=True))
            .order_by('-count')[:10]
        )
        total_genre_books = sum(g.count for g in genre_counts)
        genres = [
            {
                'name': g.name,
                'count': g.count,
                'percentage': round((g.count / total_genre_books) * 100) if total_genre_books else 0,
            }
            for g in genre_counts
        ]

        # ===== RATING DISTRIBUTION =====
        all_ratings = list(
            read_books.filter(rating__isnull=False).values_list('rating', flat=True)
        )
        rating_buckets = {i: 0 for i in range(1, 11)}
        for r in all_ratings:
            bucket = min(int(float(r)), 10)
            if bucket < 1:
                bucket = 1
            rating_buckets[bucket] += 1
        ratings = [{'rating': k, 'count': v} for k, v in rating_buckets.items()]

        # ===== READING PACE =====
        paced_books = (
            year_books
            .filter(started_at__isnull=False, finished_at__isnull=False)
            .select_related('book')
            .prefetch_related('book__authors')
        )
        pace_data = []
        for ub in paced_books:
            days = (ub.finished_at - ub.started_at).days
            if days >= 0:
                pace_data.append({
                    'days': days,
                    'title': ub.book.title,
                    'authors': [a.name for a in ub.book.authors.all()],
                    'cover': ub.book.cover_image_url if hasattr(ub.book, 'cover_image_url') else '',
                    'pages': ub.book.pages,
                })

        avg_days = round(sum(p['days'] for p in pace_data) / len(pace_data)) if pace_data else None
        fastest = min(pace_data, key=lambda x: x['days']) if pace_data else None
        slowest = max(pace_data, key=lambda x: x['days']) if pace_data else None

        pace = {
            'avg_days_per_book': avg_days,
            'total_tracked': len(pace_data),
            'fastest': fastest,
            'slowest': slowest,
        }

        # ===== ENGAGEMENT DEPTH =====
        top_engaged = (
            read_books
            .filter(quotes_count__gt=0)
            .select_related('book')
            .prefetch_related('book__authors')
            .order_by('-depth_score')[:5]
        )
        engagement = [
            {
                'title': ub.book.title,
                'authors': [a.name for a in ub.book.authors.all()],
                'cover': ub.book.cover_image_url if hasattr(ub.book, 'cover_image_url') else '',
                'quotes_count': ub.quotes_count,
                'depth_score': round(ub.depth_score, 2) if ub.depth_score else 0,
                'pages': ub.book.pages,
            }
            for ub in top_engaged
        ]

        # ===== AUTHORS =====
        author_stats = (
            Author.objects.filter(
                books__user_books__user=user,
                books__user_books__status='read',
                books__user_books__replaced_by__isnull=True,
            )
            .annotate(count=Count('books', distinct=True))
            .order_by('-count')
        )
        top_authors = [
            {'name': a.name, 'count': a.count}
            for a in author_stats[:5]
        ]
        authors = {
            'unique_count': author_stats.count(),
            'top': top_authors,
        }

        # ===== QUOTES INSIGHTS =====
        quotes_monthly_raw = (
            year_quotes
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        quotes_monthly_map = {m['month'].month: m['count'] for m in quotes_monthly_raw}
        quotes_monthly = [{'month': m, 'count': quotes_monthly_map.get(m, 0)} for m in range(1, 13)]

        most_quoted = (
            all_quotes
            .values('book__title', 'book__id')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )

        quotes_insights = {
            'total': year_quotes.count(),
            'monthly': quotes_monthly,
            'most_quoted_book': {
                'title': most_quoted['book__title'],
                'count': most_quoted['count'],
            } if most_quoted else None,
        }

        # ===== YEAR COMPARISON =====
        prev_year_count = read_books.filter(
            finished_at__year=year - 1
        ).count()
        year_comparison = {
            'current_year': year,
            'current_count': year_books.count(),
            'previous_year': year - 1,
            'previous_count': prev_year_count,
            'delta': year_books.count() - prev_year_count,
        }

        # ===== ACTIVITY HEATMAP (365 days) =====
        heatmap_start = year_start

        book_days = dict(
            read_books
            .filter(finished_at__gte=heatmap_start, finished_at__lte=year_end)
            .values('finished_at')
            .annotate(count=Count('id'))
            .values_list('finished_at', 'count')
        )
        quote_days = dict(
            year_quotes
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .values_list('date', 'count')
        )
        vocab_days = dict(
            year_vocab
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .values_list('date', 'count')
        )

        heatmap = []
        for i in range(366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365):
            day = heatmap_start + timedelta(days=i)
            if day > year_end:
                break
            b = book_days.get(day, 0)
            q = quote_days.get(day, 0)
            v = vocab_days.get(day, 0)
            heatmap.append({
                'date': day.isoformat(),
                'total': b + q + v,
                'books': b,
                'quotes': q,
                'vocabulary': v,
            })

        # ===== VOCABULARY GROWTH =====
        mastery_counts = dict(
            all_vocab.values('mastery').annotate(count=Count('id')).values_list('mastery', 'count')
        )
        vocab_monthly_raw = (
            year_vocab
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        vocab_monthly_map = {m['month'].month: m['count'] for m in vocab_monthly_raw}
        vocab_monthly = [{'month': m, 'count': vocab_monthly_map.get(m, 0)} for m in range(1, 13)]

        vocabulary = {
            'new': mastery_counts.get('new', 0),
            'learning': mastery_counts.get('learning', 0),
            'mastered': mastery_counts.get('mastered', 0),
            'total': all_vocab.count(),
            'monthly': vocab_monthly,
        }

        return Response({
            'year': year,
            'overview': overview,
            'monthly': monthly,
            'genres': genres,
            'ratings': ratings,
            'pace': pace,
            'engagement': engagement,
            'authors': authors,
            'quotes': quotes_insights,
            'year_comparison': year_comparison,
            'heatmap': heatmap,
            'vocabulary': vocabulary,
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def export_all_data(self, request):
        """Export all user data as a ZIP file containing JSON files"""
        from apps.reading.models import UserBook, Quote, VocabularyWord
        from apps.reading.models_study import StudyNote
        from apps.codex.models import JournalEntry, Manuscript
        from apps.reading.serializers import (
            UserBookListSerializer, QuoteListSerializer, VocabularyWordSerializer,
        )
        from apps.reading.serializers_study import StudyNoteListSerializer
        from apps.codex.serializers import JournalEntrySerializer, ManuscriptDetailSerializer

        user = request.user

        def to_json(serializer_data):
            return json.dumps(serializer_data, indent=2, default=str, ensure_ascii=False)

        # Gather all data
        journal_entries = JournalEntry.objects.filter(user=user)
        manuscripts = Manuscript.objects.filter(user=user).prefetch_related('chapters')
        quotes = Quote.objects.filter(user=user).select_related('book').prefetch_related('tags')
        vocabulary = VocabularyWord.objects.filter(user=user)
        study_notes = StudyNote.objects.filter(user=user).prefetch_related('tags')
        user_books = UserBook.objects.filter(user=user).select_related('book').prefetch_related('book__authors', 'book__genres')

        # Create ZIP in memory
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('journal_entries.json', to_json(JournalEntrySerializer(journal_entries, many=True).data))
            zf.writestr('manuscripts.json', to_json(ManuscriptDetailSerializer(manuscripts, many=True).data))
            zf.writestr('quotes.json', to_json(QuoteListSerializer(quotes, many=True).data))
            zf.writestr('vocabulary.json', to_json(VocabularyWordSerializer(vocabulary, many=True).data))
            zf.writestr('study_notes.json', to_json(StudyNoteListSerializer(study_notes, many=True).data))
            zf.writestr('reading_progress.json', to_json(UserBookListSerializer(user_books, many=True).data))

        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="reading_os_export_{user.id}.zip"'
        return response

    # ==================== AUTH ENDPOINTS ====================

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny],
            throttle_classes=[AuthRateThrottle], url_path='forgot-password')
    def forgot_password(self, request):
        """
        Request password reset email.
        POST /api/users/forgot-password/
        Body: {"email": "user@example.com"}
        """
        email = request.data.get('email', '').strip().lower()
        # Always return success to prevent email enumeration
        response_msg = {'message': 'If an account with this email exists, a password reset link has been sent.'}

        if not email:
            return Response(response_msg, status=status.HTTP_200_OK)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(response_msg, status=status.HTTP_200_OK)

        # Invalidate old reset tokens
        AccountToken.objects.filter(user=user, token_type='password_reset', used=False).update(used=True)

        # Create new token
        token = AccountToken.objects.create(user=user, token_type='password_reset')

        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token.token}"
        try:
            send_mail(
                subject='Reading OS - Password Reset',
                message=f'Click this link to reset your password: {reset_url}\n\nThis link expires in 1 hour.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")

        return Response(response_msg, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny],
            throttle_classes=[AuthRateThrottle], url_path='reset-password')
    def reset_password(self, request):
        """
        Reset password using token.
        POST /api/users/reset-password/
        Body: {"token": "uuid", "password": "newpass", "password_confirm": "newpass"}
        """
        token_str = request.data.get('token')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')

        if not all([token_str, password, password_confirm]):
            return Response({'error': 'Token, password, and password confirmation are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if password != password_confirm:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = AccountToken.objects.get(token=token_str, token_type='password_reset', used=False)
        except AccountToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        if token.is_expired:
            return Response({'error': 'Token has expired. Please request a new one.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength
        try:
            validate_password(password, user=token.user)
        except DjangoValidationError as e:
            return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        token.user.set_password(password)
        token.user.save()
        token.used = True
        token.save()

        return Response({'message': 'Password has been reset successfully.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated],
            url_path='change-password')
    def change_password(self, request):
        """
        Change password for authenticated user.
        POST /api/users/change-password/
        Body: {"current_password": "...", "new_password": "...", "new_password_confirm": "..."}
        """
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        if not all([current_password, new_password, new_password_confirm]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != new_password_confirm:
            return Response({'error': 'New passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=request.user)
        except DjangoValidationError as e:
            return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()

        return Response({'message': 'Password changed successfully.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated],
            url_path='send-verification')
    def send_verification(self, request):
        """
        Send email verification link.
        POST /api/users/send-verification/
        """
        user = request.user
        if user.email_verified:
            return Response({'message': 'Email is already verified.'})

        # Invalidate old verification tokens
        AccountToken.objects.filter(user=user, token_type='email_verify', used=False).update(used=True)

        token = AccountToken.objects.create(user=user, token_type='email_verify')
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"

        try:
            send_mail(
                subject='Reading OS - Verify Your Email',
                message=f'Click this link to verify your email: {verify_url}\n\nThis link expires in 7 days.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return Response({'error': 'Failed to send email. Please try again later.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Verification email sent.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny],
            url_path='verify-email')
    def verify_email(self, request):
        """
        Verify email using token.
        POST /api/users/verify-email/
        Body: {"token": "uuid"}
        """
        token_str = request.data.get('token')
        if not token_str:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = AccountToken.objects.get(token=token_str, token_type='email_verify', used=False)
        except AccountToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        if token.is_expired:
            return Response({'error': 'Token has expired. Please request a new one.'},
                            status=status.HTTP_400_BAD_REQUEST)

        token.user.email_verified = True
        token.user.save(update_fields=['email_verified'])
        token.used = True
        token.save()

        return Response({'message': 'Email verified successfully.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated],
            url_path='delete-account')
    def delete_account(self, request):
        """
        Delete user account permanently.
        POST /api/users/delete-account/
        Body: {"password": "...", "confirm": true}
        """
        password = request.data.get('password')
        confirm = request.data.get('confirm', False)

        if not password:
            return Response({'error': 'Password is required to delete account.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not confirm:
            return Response({'error': 'Please confirm account deletion.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({'error': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        logger.info(f"User {user.id} ({user.email}) requested account deletion.")

        # Transfer circle ownership before deletion
        from apps.social.models import Circle, CircleMembership
        owned_circles = Circle.objects.filter(creator=user)
        for circle in owned_circles:
            # Find oldest admin or member to transfer ownership
            next_admin = CircleMembership.objects.filter(
                circle=circle, role__in=['admin', 'moderator']
            ).exclude(user=user).order_by('joined_at').first()

            if next_admin:
                circle.creator = next_admin.user
                circle.save(update_fields=['creator'])
            else:
                next_member = CircleMembership.objects.filter(
                    circle=circle
                ).exclude(user=user).order_by('joined_at').first()
                if next_member:
                    circle.creator = next_member.user
                    next_member.role = 'admin'
                    next_member.save(update_fields=['role'])
                    circle.save(update_fields=['creator'])
                # If no other members, circle will be deleted via cascade

        user.delete()
        return Response({'message': 'Account deleted successfully.'}, status=status.HTTP_200_OK)

