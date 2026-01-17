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
            'user': UserSerializer(user).data,
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
            'user': UserSerializer(user).data,
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
        serializer = UserDetailSerializer(request.user)
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
        return Response(UserDetailSerializer(request.user).data)
    
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
        Search users by name or username.
        GET /api/users/search/?q=query
        """
        query = request.query_params.get('q', '').strip()

        if not query or len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search in first_name, last_name, username
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
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
            user_serialized = UserSerializer(user).data

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

        # Serialize user data
        user_data = UserDetailSerializer(user).data
        user_data.update({
            'is_following': is_following,
            'is_follower': is_follower,
            'friendship_id': friendship_id,
            'followers_count': followers_count,
            'following_count': following_count,
            'books_read_count': books_read_count,
            'quotes_count': quotes_count,
            'top_genres': list(top_genres),
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

        # Get user's books
        queryset = UserBook.objects.filter(user=user).select_related(
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
            follower_serialized = UserSerializer(follower).data

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
            followed_serialized = UserSerializer(followed_user).data

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

