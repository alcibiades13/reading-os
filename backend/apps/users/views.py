import io
import json
import zipfile
from django.http import HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Count

from apps.users.models import User, UserProfile
from apps.users.serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
)


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
            # Anyone can register
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only owner can modify
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
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
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
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

            # Debug logging
            all_friendships = Friendship.objects.filter(
                from_user=request.user,
                to_user=user
            )
            print(f"DEBUG Profile API - Current user: {request.user.id}, Viewed user: {user.id}")
            print(f"DEBUG Profile API - All friendships from {request.user.id} to {user.id}: {list(all_friendships.values('id', 'from_user_id', 'to_user_id', 'status'))}")
            print(f"DEBUG Profile API - Following friendship: {following_friendship}")
            if following_friendship:
                print(f"DEBUG Profile API - Following friendship ID: {following_friendship.id}")

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
            current_user_book_ids = set(
                UserBook.objects.filter(
                    user=request.user,
                    replaced_by__isnull=True
                ).values_list('book_id', flat=True)
            )
            shared_user_books = UserBook.objects.filter(
                user=user,
                replaced_by__isnull=True,
                book_id__in=current_user_book_ids
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
            current_total = len(current_user_book_ids)
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

