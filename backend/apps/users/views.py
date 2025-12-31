from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

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
