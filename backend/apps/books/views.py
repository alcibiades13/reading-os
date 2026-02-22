from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg

from apps.books.models import Author, AuthorGroup, Publisher, Genre, Tag, Book
from apps.books.serializers import (
    AuthorSerializer,
    PublisherSerializer,
    GenreSerializer,
    TagSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookCreateSerializer,
    BookImportSerializer,
)
from apps.books.filters import UnaccentSearchFilter


class AuthorViewSet(viewsets.ModelViewSet):
    """ViewSet for Author model"""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [UnaccentSearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'bio']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get all books by this author (including alias authors if grouped)."""
        author = self.get_object()

        if author.author_group_id:
            alias_ids = author.author_group.members.values_list('id', flat=True)
            books = (
                Book.objects.filter(authors__id__in=alias_ids)
                .distinct()
                .select_related('publisher')
                .prefetch_related('authors')
            )
        else:
            books = author.books.all().select_related('publisher').prefetch_related('authors')

        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def link_author(self, request, pk=None):
        """
        Link this author to another as name aliases (same person, different spellings).
        Creates AuthorGroup if needed.
        """
        author1 = self.get_object()
        author2_id = request.data.get('author_id')

        if not author2_id:
            return Response({'error': 'author_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            author2 = Author.objects.get(id=author2_id)
        except Author.DoesNotExist:
            return Response({'error': 'Author not found'}, status=status.HTTP_404_NOT_FOUND)

        if author1.id == author2.id:
            return Response({'error': 'Cannot link author to itself'}, status=status.HTTP_400_BAD_REQUEST)

        # If either has a group, use that; else create new
        if author1.author_group:
            group = author1.author_group
        elif author2.author_group:
            group = author2.author_group
        else:
            group = AuthorGroup.objects.create(canonical_name=author1.name)
            author1.is_primary_alias = True
            author1.save()

        author1.author_group = group
        author2.author_group = group
        author1.save()
        author2.save()

        return Response({
            'success': True,
            'author_group_id': group.id,
            'canonical_name': group.canonical_name,
            'members_count': group.members.count(),
        })

    @action(detail=True, methods=['get'])
    def potential_aliases(self, request, pk=None):
        """
        Find potential alias authors (same person, different name spelling).
        Uses fuzzy matching on author names.
        """
        from difflib import SequenceMatcher

        author = self.get_object()
        author_name_lower = author.name.lower().strip()

        candidates = Author.objects.exclude(id=author.id)
        if author.author_group:
            candidates = candidates.exclude(author_group=author.author_group)

        matches = []
        for candidate in candidates:
            candidate_name_lower = candidate.name.lower().strip()
            similarity = SequenceMatcher(None, author_name_lower, candidate_name_lower).ratio()

            if similarity >= 0.70:
                matches.append({
                    'id': candidate.id,
                    'name': candidate.name,
                    'slug': candidate.slug,
                    'photo': candidate.photo,
                    'bio': (candidate.bio or '')[:200],
                    'books_count': candidate.books.count(),
                    'similarity': round(similarity, 3),
                })

        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return Response(matches[:10])


class PublisherViewSet(viewsets.ModelViewSet):
    """ViewSet for Publisher model"""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'country']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class GenreViewSet(viewsets.ModelViewSet):
    """ViewSet for Genre model"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optionally filter by parent genre"""
        queryset = Genre.objects.all()
        parent_id = self.request.query_params.get('parent', None)
        
        if parent_id == 'null' or parent_id == '':
            # Get top-level genres (no parent)
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            # Get subgenres of specific parent
            queryset = queryset.filter(parent_id=parent_id)
        
        return queryset.prefetch_related('subgenres')


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag model"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optionally filter by category"""
        queryset = Tag.objects.all()
        category = self.request.query_params.get('category', None)
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset


class BookViewSet(viewsets.ModelViewSet):
    """ViewSet for Book model"""
    queryset = Book.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [UnaccentSearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle', 'isbn', 'authors__name', 'description']
    ordering_fields = ['title', 'published_date', 'created_at', 'pages']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return BookCreateSerializer
        elif self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            return BookDetailSerializer
        return BookListSerializer
    
    def get_queryset(self):
        """Filter and optimize queryset"""
        queryset = Book.objects.all().select_related('publisher').prefetch_related(
            'authors',
            'genres',
            'tags',
        )
        
        # Filter by language
        language = self.request.query_params.get('language', None)
        if language:
            queryset = queryset.filter(language=language)
        
        # Filter by genre
        genre_id = self.request.query_params.get('genre', None)
        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(authors__id=author_id)
        
        # Filter by tag
        tag_id = self.request.query_params.get('tag', None)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # Filter by ISBN
        isbn = self.request.query_params.get('isbn', None)
        if isbn:
            queryset = queryset.filter(isbn=isbn)
        
        return queryset.distinct()


    @action(detail=True, methods=['get'])
    def readers(self, request, pk=None):
        """Get users who have this book"""
        book = self.get_object()
        from apps.reading.models import UserBook
        from apps.users.serializers import UserSerializer
        
        user_books = UserBook.objects.filter(book=book).select_related('user')
        users = [ub.user for ub in user_books]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def quotes(self, request, pk=None):
        """Get public quotes from this book"""
        book = self.get_object()
        from apps.reading.models import Quote
        from apps.reading.serializers import QuoteListSerializer

        quotes = Quote.objects.filter(
            book=book,
            is_public=True
        ).select_related('user', 'book').prefetch_related('tags')

        serializer = QuoteListSerializer(quotes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def community_activity(self, request, pk=None):
        """
        Get community activity for this book:
        - Reviews from other users (with truncated content)
        - Public quotes from other users
        Excludes the current user's content.
        """
        book = self.get_object()
        from apps.reading.models import UserBook, Quote
        import re

        def get_avatar_url(user):
            """Safely get avatar URL from user"""
            if user.avatar and hasattr(user.avatar, 'url'):
                return user.avatar.url
            return None

        # Get book group to include all editions
        book_ids = [book.id]
        if book.book_group:
            book_ids = list(book.book_group.editions.values_list('id', flat=True))

        # Get reviews from other users (excluding current user)
        reviews_qs = UserBook.objects.filter(
            book_id__in=book_ids,
            review__isnull=False,
            is_public=True  # Only public reviews
        ).exclude(
            review=''
        ).select_related('user', 'book').order_by('-updated_at')

        # Exclude current user if authenticated
        if request.user.is_authenticated:
            reviews_qs = reviews_qs.exclude(user=request.user)

        # Limit to 10 reviews
        reviews_data = []
        for ub in reviews_qs[:10]:
            # Strip HTML and truncate review
            plain_text = re.sub(r'<[^>]+>', '', ub.review or '')
            plain_text = plain_text.strip()
            truncated = plain_text[:300] + '...' if len(plain_text) > 300 else plain_text

            reviews_data.append({
                'id': ub.id,
                'user': {
                    'id': ub.user.id,
                    'first_name': ub.user.first_name,
                    'last_name': ub.user.last_name,
                    'avatar': get_avatar_url(ub.user),
                },
                'rating': float(ub.rating) if ub.rating else None,
                'status': ub.status,
                'review_preview': truncated,
                'has_full_review': len(plain_text) > 300,
                'finished_at': ub.finished_at.isoformat() if ub.finished_at else None,
                'updated_at': ub.updated_at.isoformat() if ub.updated_at else None,
                'book_id': ub.book_id,
            })

        # Get public quotes from other users
        quotes_qs = Quote.objects.filter(
            book_id__in=book_ids,
            is_public=True
        ).select_related('user', 'book').prefetch_related('tags').order_by('-created_at')

        # Exclude current user if authenticated
        if request.user.is_authenticated:
            quotes_qs = quotes_qs.exclude(user=request.user)

        # Limit to 10 quotes
        quotes_data = []
        for quote in quotes_qs[:10]:
            quotes_data.append({
                'id': quote.id,
                'user': {
                    'id': quote.user.id,
                    'first_name': quote.user.first_name,
                    'last_name': quote.user.last_name,
                    'avatar': get_avatar_url(quote.user),
                },
                'text': quote.text[:500] + '...' if len(quote.text) > 500 else quote.text,
                'page_number': quote.page_number,
                'chapter': quote.chapter,
                'is_favorite': quote.is_favorite,
                'created_at': quote.created_at.isoformat() if quote.created_at else None,
                'tags': [{'id': t.id, 'name': t.name} for t in quote.tags.all()],
            })

        return Response({
            'reviews': reviews_data,
            'quotes': quotes_data,
            'reviews_count': reviews_qs.count(),
            'quotes_count': quotes_qs.count(),
        })

    @action(detail=True, methods=['get'], url_path='review/(?P<user_id>[^/.]+)')
    def user_review(self, request, pk=None, user_id=None):
        """
        Get a specific user's full review for this book.
        URL: /api/books/{book_id}/review/{user_id}/
        """
        book = self.get_object()
        from apps.reading.models import UserBook
        from django.contrib.auth import get_user_model

        User = get_user_model()

        def get_avatar_url(user):
            """Safely get avatar URL from user"""
            if user.avatar and hasattr(user.avatar, 'url'):
                return user.avatar.url
            return None

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get book group to include all editions
        book_ids = [book.id]
        if book.book_group:
            book_ids = list(book.book_group.editions.values_list('id', flat=True))

        # Get user's review for this book (or any edition)
        user_book = UserBook.objects.filter(
            book_id__in=book_ids,
            user=user,
            review__isnull=False,
            is_public=True
        ).exclude(review='').select_related('user', 'book').first()

        if not user_book:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get like/comment counts
        from apps.social.models import ReviewLike, ReviewComment
        likes_count = ReviewLike.objects.filter(user_book=user_book).count()
        comments_count = ReviewComment.objects.filter(user_book=user_book).count()
        has_liked = False
        if request.user.is_authenticated:
            has_liked = ReviewLike.objects.filter(
                user_book=user_book, user=request.user
            ).exists()

        return Response({
            'id': user_book.id,
            'user': {
                'id': user_book.user.id,
                'first_name': user_book.user.first_name,
                'last_name': user_book.user.last_name,
                'avatar': get_avatar_url(user_book.user),
            },
            'book': {
                'id': user_book.book.id,
                'title': user_book.book.title,
                'cover_image': user_book.book.cover_image,
                'authors': [{'id': a.id, 'name': a.name} for a in user_book.book.authors.all()],
            },
            'rating': float(user_book.rating) if user_book.rating else None,
            'status': user_book.status,
            'review': user_book.review,  # Full review HTML
            'finished_at': user_book.finished_at.isoformat() if user_book.finished_at else None,
            'started_at': user_book.started_at.isoformat() if user_book.started_at else None,
            'updated_at': user_book.updated_at.isoformat() if user_book.updated_at else None,
            'likes_count': likes_count,
            'comments_count': comments_count,
            'has_liked': has_liked,
        })

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular books with smart scoring"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import F, Q, FloatField, Value
        from django.db.models.functions import Coalesce

        thirty_days_ago = timezone.now() - timedelta(days=30)

        books = Book.objects.annotate(
            # Count total readers
            readers_count=Count('user_books', distinct=True),

            # Count recent readers (last 30 days)
            recent_readers=Count(
                'user_books',
                filter=Q(user_books__created_at__gte=thirty_days_ago),
                distinct=True
            ),

            # Average rating
            avg_rating=Avg('user_books__rating'),

            # Quote count (engagement)
            quote_count=Count('quotes', filter=Q(quotes__is_public=True))
        ).filter(
            readers_count__gte=2  # Minimum 2 readers to appear
        ).annotate(
            # Popularity score: weighted combination
            popularity_score=(
                F('readers_count') * 1.0 +  # Total readers weight
                F('recent_readers') * 3.0 +  # Recent activity weight (3x)
                Coalesce(F('avg_rating'), Value(0.0), output_field=FloatField()) * 2.0 +  # Rating weight
                F('quote_count') * 0.5  # Quote engagement
            )
        ).order_by('-popularity_score')[:20]

        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Books trending in last 7 days - perfect for cold start"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q

        seven_days_ago = timezone.now() - timedelta(days=7)

        books = Book.objects.annotate(
            recent_activity=Count(
                'user_books',
                filter=Q(user_books__created_at__gte=seven_days_ago)
            )
        ).filter(
            recent_activity__gte=1
        ).order_by('-recent_activity')[:10]

        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Curated featured books - great for cold start"""
        books = Book.objects.filter(
            is_featured=True
        ).order_by('featured_order')[:20]

        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added books"""
        books = Book.objects.all().order_by('-created_at')[:20]
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Custom update to handle authors and publisher"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Extract special fields that need custom handling
        authors = request.data.get('authors', None)
        publisher_name = request.data.get('publisher_name', None)

        # Prepare data for serializer (exclude authors for now)
        serializer_data = request.data.copy()
        if 'authors' in serializer_data:
            del serializer_data['authors']
        if 'publisher_name' in serializer_data:
            del serializer_data['publisher_name']

        # Handle publisher
        if publisher_name:
            publisher, _ = Publisher.objects.get_or_create(
                name=publisher_name,
                defaults={'country': ''}
            )
            serializer_data['publisher'] = publisher.id

        # Update book instance
        serializer = self.get_serializer(instance, data=serializer_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Handle authors (many-to-many)
        if authors is not None:
            author_objs = []
            for author_name in authors:
                if author_name and author_name.strip():
                    author, _ = Author.objects.get_or_create(
                        name=author_name.strip(),
                        defaults={'bio': ''}
                    )
                    author_objs.append(author)
            instance.authors.set(author_objs)

        # Return updated book with all relations
        book_with_relations = Book.objects.select_related('publisher').prefetch_related(
            'authors', 'genres', 'tags'
        ).get(id=instance.id)

        output_serializer = BookDetailSerializer(book_with_relations)
        return Response(output_serializer.data)

    def perform_destroy(self, instance):
        """Override destroy to handle deletion without errors"""
        from apps.reading.models import UserBook, Quote

        # Don't delete user data! Just unlink it from the book being deleted
        # Set book to NULL for quotes (they can still have book_title and book_author)
        Quote.objects.filter(book=instance).update(book=None)

        # Delete user_books associated with this book (these are reading progress, not quotes)
        UserBook.objects.filter(book=instance).delete()

        # Now delete the book itself
        instance.delete()

    @action(detail=False, methods=['post'])
    def scrape_delfi(self, request):
        """Scrape book from Delfi.rs URL"""
        from utils.delfi_scraper import scrape_delfi_book

        url = request.data.get('url')
        if not url:
            return Response(
                {'error': 'URL parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Scrape the book
        try:
            book_data = scrape_delfi_book(url)
            if not book_data:
                return Response(
                    {'error': 'Failed to scrape book data from URL'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Transform Delfi data to match our import format
            publisher = book_data.get('publisher')
            # Fix: publisher_name can be too long, limit to reasonable length
            if publisher and len(publisher) > 200:
                publisher = None  # Skip if too long (scraper error)

            transformed_data = {
                'title': book_data.get('title'),
                'subtitle': book_data.get('subtitle'),
                'description': book_data.get('description'),
                'isbn_13': book_data.get('isbn_13'),
                'isbn_10': book_data.get('isbn_10'),
                'cover_image_url': book_data.get('cover_image_url'),
                'published_date': book_data.get('published_date'),
                'page_count': book_data.get('page_count'),
                'language': book_data.get('language', 'sr'),
                'authors': book_data.get('authors', []),
                'publisher_name': publisher,
                'genres': book_data.get('categories', []),
                'source': 'delfi_scrape',
                'delfi_id': book_data.get('delfi_id'),
            }

            return Response(transformed_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error scraping Delfi.rs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def import_book(self, request):
        """Import book from external source (Google Books, etc)"""
        try:
            book_data = request.data.get('book', request.data)
            add_to_library = request.data.get('addToLibrary', False)
            library_data = request.data.get('libraryData', None)

            # Import the book
            serializer = BookImportSerializer(data=book_data)

            if serializer.is_valid():
                # Check if book already exists by ISBN
                isbn = serializer.validated_data.get('isbn_13') or serializer.validated_data.get('isbn_10')
                existing_book = None

                if isbn:
                    existing_book = Book.objects.filter(isbn=isbn).first()

                if existing_book:
                    book = existing_book
                else:
                    book = serializer.save()

                # Add to user's library if requested
                if add_to_library and library_data:
                    from apps.reading.models import UserBook
                    from datetime import date

                    # Check if user already has this book in their library
                    existing_user_book = UserBook.objects.filter(
                        user=request.user,
                        book=book
                    ).first()

                    if existing_user_book:
                        # User already has this book - return error
                        return Response(
                            {
                                'error': 'You already have this book in your library',
                                'book': BookDetailSerializer(book).data
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Prepare defaults for UserBook
                    defaults = {
                        'status': library_data.get('status', 'want_to_read'),
                    }

                    # Add rating if provided and status is 'read'
                    if library_data.get('rating') and library_data.get('status') == 'read':
                        defaults['rating'] = library_data['rating']

                    # Set started_at for currently_reading
                    if library_data.get('status') == 'currently_reading':
                        defaults['started_at'] = date.today()

                    # Set finished_at for read
                    if library_data.get('status') == 'read':
                        defaults['finished_at'] = date.today()

                    # Create the UserBook entry
                    user_book = UserBook.objects.create(
                        user=request.user,
                        book=book,
                        **defaults
                    )

                # Return full book details with proper select_related/prefetch_related
                book_with_relations = Book.objects.select_related('publisher').prefetch_related(
                    'authors', 'genres', 'tags'
                ).get(id=book.id)

                detail_serializer = BookDetailSerializer(book_with_relations)
                return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the full error for debugging
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def switch_edition(self, request, pk=None):
        """
        Switch from current book to another edition in the same group.
        Transfers user's reading data to the new edition.
        """
        old_book = self.get_object()
        new_book_id = request.data.get('new_book_id')

        if not new_book_id:
            return Response({'error': 'new_book_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_book = Book.objects.get(id=new_book_id)
        except Book.DoesNotExist:
            return Response({'error': 'New book not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate books are in same group
        if not old_book.book_group or old_book.book_group != new_book.book_group:
            return Response({'error': 'Books not in same group'}, status=status.HTTP_400_BAD_REQUEST)

        # Get user's old UserBook
        from apps.reading.models import UserBook, Quote, VocabularyWord
        from apps.reading.models_study import StudyNote

        old_userbook = UserBook.objects.filter(
            user=request.user,
            book=old_book
        ).first()

        if not old_userbook:
            return Response({'error': 'No reading data for old book'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already has new edition (ACTIVE)
        existing_active_userbook = UserBook.objects.filter(
            user=request.user,
            book=new_book,
            replaced_by__isnull=True
        ).first()

        if existing_active_userbook:
            return Response({'error': 'Already tracking new edition'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if there's a replaced UserBook for the new book (from previous switch)
        # If so, we'll reactivate it instead of creating a new one
        existing_replaced_userbook = UserBook.objects.filter(
            user=request.user,
            book=new_book,
            replaced_by__isnull=False
        ).first()

        # Create or reactivate UserBook with transferred data
        # Calculate transferred page number (default to 0 if can't calculate)
        transferred_page = self._transfer_page_number(
            old_userbook.current_page,
            old_book.pages,
            new_book.pages
        ) if old_book.pages and new_book.pages and old_userbook.current_page else 0

        if existing_replaced_userbook:
            # Reactivate the existing replaced UserBook
            new_userbook = existing_replaced_userbook
            new_userbook.status = old_userbook.status
            new_userbook.rating = old_userbook.rating
            new_userbook.review = old_userbook.review
            new_userbook.is_favorite = old_userbook.is_favorite
            new_userbook.started_at = old_userbook.started_at
            new_userbook.finished_at = old_userbook.finished_at
            new_userbook.is_public = old_userbook.is_public
            new_userbook.current_page = transferred_page
            new_userbook.replaced_by = None  # Reactivate
            new_userbook.save()
        else:
            # Create new UserBook
            new_userbook = UserBook.objects.create(
                user=request.user,
                book=new_book,
                status=old_userbook.status,
                rating=old_userbook.rating,
                review=old_userbook.review,
                is_favorite=old_userbook.is_favorite,
                started_at=old_userbook.started_at,
                finished_at=old_userbook.finished_at,
                is_public=old_userbook.is_public,
                current_page=transferred_page
            )

        # If reactivating an existing UserBook, delete its old quotes first
        if existing_replaced_userbook:
            Quote.objects.filter(user=request.user, book=new_book).delete()

        # Transfer quotes (with proportional page numbers)
        old_quotes = Quote.objects.filter(user=request.user, book=old_book)
        transferred_quotes = 0
        for old_quote in old_quotes:
            Quote.objects.create(
                user=request.user,
                book=new_book,
                user_book=new_userbook,
                book_title=new_book.title,
                book_author=', '.join([a.name for a in new_book.authors.all()]),
                text=old_quote.text,
                page_number=self._transfer_page_number(
                    old_quote.page_number,
                    old_book.pages,
                    new_book.pages
                ) if old_book.pages and new_book.pages and old_quote.page_number else None,
                chapter=old_quote.chapter,
                note=old_quote.note,
                is_favorite=old_quote.is_favorite,
                is_public=old_quote.is_public,
            )
            transferred_quotes += 1

        # Transfer study notes
        transferred_notes = StudyNote.objects.filter(
            user=request.user, book=old_book
        ).update(book=new_book, user_book=new_userbook)

        # Transfer vocabulary words
        transferred_words = VocabularyWord.objects.filter(
            user=request.user, book=old_book
        ).update(book=new_book)

        # Mark old UserBook as replaced (KEEP for history, don't delete)
        old_userbook.replaced_by = new_userbook
        old_userbook.save()

        return Response({
            'success': True,
            'new_userbook_id': new_userbook.id,
            'new_book_id': new_book.id,
            'transferred_quotes': transferred_quotes,
            'transferred_notes': transferred_notes,
            'transferred_words': transferred_words,
            'old_userbook_preserved': True
        })

    def _transfer_page_number(self, old_page, old_total, new_total):
        """Transfer page number proportionally between editions"""
        if not old_page or not old_total or not new_total:
            return None
        ratio = old_page / old_total
        return int(ratio * new_total)

    @action(detail=True, methods=['post'])
    def link_edition(self, request, pk=None):
        """
        Link this book to another as editions of same work.
        Creates BookGroup if needed.
        """
        book1 = self.get_object()
        book2_id = request.data.get('book_id')

        if not book2_id:
            return Response({'error': 'book_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book2 = Book.objects.get(id=book2_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        from apps.books.models import BookGroup

        # If either has a group, use that; else create new
        if book1.book_group:
            group = book1.book_group
        elif book2.book_group:
            group = book2.book_group
        else:
            # Create new group
            group = BookGroup.objects.create(
                canonical_title=book1.title,
                description=book1.description
            )
            group.canonical_authors.set(book1.authors.all())
            book1.is_primary_edition = True
            book1.save()

        # Link both books to group
        book1.book_group = group
        book2.book_group = group
        book1.save()
        book2.save()

        # Update stats
        group.update_stats()

        # Auto-link authors with similar names across the two books
        from difflib import SequenceMatcher as SM

        for a1 in book1.authors.all():
            for a2 in book2.authors.all():
                if a1.id == a2.id:
                    continue
                if a1.author_group_id and a2.author_group_id and a1.author_group_id == a2.author_group_id:
                    continue

                sim = SM(None, a1.name.lower(), a2.name.lower()).ratio()
                if sim >= 0.75:
                    if a1.author_group:
                        ag = a1.author_group
                    elif a2.author_group:
                        ag = a2.author_group
                    else:
                        primary_author = a1 if book1.is_primary_edition else a2
                        ag = AuthorGroup.objects.create(canonical_name=primary_author.name)
                        primary_author.is_primary_alias = True
                        primary_author.save()

                    a1.author_group = ag
                    a2.author_group = ag
                    a1.save()
                    a2.save()

        return Response({
            'success': True,
            'book_group_id': group.id,
            'editions_count': group.editions_count
        })

    @action(detail=True, methods=['get'])
    def potential_editions(self, request, pk=None):
        """
        Find potential editions of this book based on:
        - Similar title (fuzzy match)
        - Same or similar authors
        - Different ISBN (or one/both missing ISBN)
        """
        from difflib import SequenceMatcher

        book = self.get_object()

        # Skip if already in a group with editions
        if book.book_group and book.book_group.editions.count() > 1:
            return Response([])

        # Get author names for this book
        author_names = set(author.name.lower().strip() for author in book.authors.all())

        if not author_names:
            return Response([])

        # Find candidates with overlapping authors
        candidates_qs = Book.objects.exclude(id=book.id)

        # Only exclude same book_group if book has a group
        if book.book_group:
            candidates_qs = candidates_qs.exclude(book_group=book.book_group)

        candidates = candidates_qs.prefetch_related('authors', 'publisher')

        matches = []
        book_title_lower = book.title.lower().strip()

        for candidate in candidates:
            # Check author overlap
            candidate_author_names = set(author.name.lower().strip() for author in candidate.authors.all())

            if not candidate_author_names:
                continue

            # Calculate author similarity
            author_overlap = len(author_names & candidate_author_names)
            author_similarity = 0.0

            if author_overlap > 0:
                # Exact match on at least one author
                author_similarity = 1.0
            else:
                # Check for similar author names (handles "Hermann Hesse" vs "Herman Hese")
                max_author_sim = 0.0
                for author1 in author_names:
                    for author2 in candidate_author_names:
                        sim = SequenceMatcher(None, author1, author2).ratio()
                        max_author_sim = max(max_author_sim, sim)
                author_similarity = max_author_sim

            # Skip if authors are too different
            if author_similarity < 0.75:
                continue

            # Calculate title similarity
            candidate_title_lower = candidate.title.lower().strip()
            title_similarity = SequenceMatcher(None, book_title_lower, candidate_title_lower).ratio()

            # Calculate combined score (weighted: title 70%, author 30%)
            combined_score = (title_similarity * 0.7) + (author_similarity * 0.3)

            # Only include if high enough similarity
            if combined_score >= 0.75:
                # Check if ISBNs are different (or missing)
                isbn_different = True
                if book.isbn and candidate.isbn:
                    isbn_different = book.isbn != candidate.isbn

                if isbn_different:
                    matches.append({
                        'id': candidate.id,
                        'title': candidate.title,
                        'subtitle': candidate.subtitle or '',
                        'language': candidate.language,
                        'isbn': candidate.isbn,
                        'pages': candidate.pages,
                        'cover_image': candidate.cover_image,
                        'publisher': candidate.publisher.name if candidate.publisher else None,
                        'published_date': candidate.published_date,
                        'authors': [{'id': a.id, 'name': a.name} for a in candidate.authors.all()],
                        'similarity': round(combined_score, 3),
                        'title_similarity': round(title_similarity, 3),
                        'author_similarity': round(author_similarity, 3),
                    })

        # Sort by combined score (descending)
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        # Limit to top 10 matches
        return Response(matches[:10])

    @action(detail=False, methods=['post'])
    def import_goodreads_csv(self, request):
        """Import books from Goodreads CSV export"""
        import csv
        import io
        from datetime import datetime
        from apps.reading.models import UserBook
        from django.db.models.signals import post_save
        from apps.social import signals as social_signals

        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Disconnect feed item creation signal during bulk import
        post_save.disconnect(social_signals.create_userbook_feed_item, sender=UserBook)

        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))

            imported_count = 0
            skipped_count = 0
            errors = []
            created_books = []
            updated_books = []

            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 = header)
                try:
                    # Extract book data from CSV
                    title = row.get('Title', '').strip()
                    if not title:
                        skipped_count += 1
                        continue

                    # Clean ISBN (Goodreads wraps in ="" ... "")
                    isbn_raw = row.get('ISBN13', '') or row.get('ISBN', '')
                    isbn = isbn_raw.replace('="', '').replace('"', '').strip()

                    # Parse author
                    author_name = row.get('Author', '').strip()

                    # Find or create book
                    book = None
                    if isbn:
                        book = Book.objects.filter(isbn=isbn).first()

                    # If no ISBN match, try to find by title + author
                    if not book and title and author_name:
                        # Try exact title match with author
                        book = Book.objects.filter(
                            title__iexact=title,
                            authors__name__iexact=author_name
                        ).first()

                        # If still not found, try with title only (for common cases)
                        if not book:
                            book = Book.objects.filter(title__iexact=title).first()

                    if not book:
                        # Create new book
                        publisher_name = row.get('Publisher', '').strip()
                        publisher = None
                        if publisher_name:
                            publisher, _ = Publisher.objects.get_or_create(
                                name=publisher_name[:200],  # Limit length
                                defaults={'country': ''}
                            )

                        # Parse pages
                        pages_str = row.get('Number of Pages', '').strip()
                        pages = None
                        try:
                            pages = int(pages_str) if pages_str else None
                        except ValueError:
                            pass

                        # Parse year
                        year_str = row.get('Year Published', '') or row.get('Original Publication Year', '')
                        year_str = year_str.strip()
                        published_date = None
                        if year_str:
                            try:
                                published_date = f"{int(float(year_str))}-01-01"
                            except ValueError:
                                pass

                        # Extract Goodreads cover URL and language from Book Id
                        cover_image_url = None
                        book_language = ''  # Empty fallback (not 'en')
                        goodreads_book_id = row.get('Book Id', '').strip()
                        if goodreads_book_id:
                            # Try to fetch Goodreads page and extract cover + language
                            try:
                                import requests
                                from bs4 import BeautifulSoup

                                gr_url = f'https://www.goodreads.com/book/show/{goodreads_book_id}'
                                response = requests.get(gr_url, timeout=5, headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                })
                                if response.status_code == 200:
                                    soup = BeautifulSoup(response.text, 'html.parser')

                                    # Extract og:image meta tag
                                    og_image = soup.find('meta', property='og:image')
                                    if og_image and og_image.get('content'):
                                        cover_image_url = og_image['content']

                                    # Extract language from DescList structure
                                    # HTML structure: <dl class="DescList"><div class="DescListItem"><dt>Language</dt><dd>...<div data-testid="contentContainer">Serbian</div>
                                    desc_list = soup.find('dl', class_='DescList')
                                    if desc_list:
                                        items = desc_list.find_all('div', class_='DescListItem')
                                        for item in items:
                                            dt = item.find('dt')
                                            if dt and dt.get_text(strip=True) == 'Language':
                                                # Found Language item, extract value from dd
                                                dd = item.find('dd')
                                                if dd:
                                                    content_div = dd.find('div', {'data-testid': 'contentContainer'})
                                                    if content_div:
                                                        lang_text = content_div.get_text(strip=True)
                                                        if lang_text:
                                                            # Map common languages to codes
                                                            lang_map = {
                                                                'Serbian': 'sr',
                                                                'English': 'en',
                                                                'Spanish': 'es',
                                                                'French': 'fr',
                                                                'German': 'de',
                                                                'Italian': 'it',
                                                                'Russian': 'ru',
                                                                'Japanese': 'ja',
                                                                'Chinese': 'zh',
                                                                'Portuguese': 'pt',
                                                                'Dutch': 'nl',
                                                                'Polish': 'pl',
                                                                'Czech': 'cs',
                                                                'Croatian': 'hr',
                                                            }
                                                            book_language = lang_map.get(lang_text, '')
                                                            break
                            except Exception as e:
                                # Silently fail - will use empty string
                                pass

                        # Create book
                        book = Book.objects.create(
                            title=title,
                            isbn=isbn if isbn else None,
                            publisher=publisher,
                            pages=pages,
                            published_date=published_date,
                            language=book_language,
                            cover_image=cover_image_url if cover_image_url else '',
                        )

                        # Add author
                        if author_name:
                            author, _ = Author.objects.get_or_create(
                                name=author_name,
                                defaults={'bio': ''}
                            )
                            book.authors.add(author)

                        created_books.append(book.id)

                    # Create or update UserBook
                    # Map Goodreads shelf to our status
                    shelf = row.get('Exclusive Shelf', '').strip()
                    status_mapping = {
                        'read': 'read',
                        'currently-reading': 'currently_reading',
                        'to-read': 'want_to_read',
                    }
                    book_status = status_mapping.get(shelf, 'want_to_read')

                    # Check if UserBook already exists
                    user_book, created = UserBook.objects.get_or_create(
                        user=request.user,
                        book=book,
                        defaults={'status': book_status}
                    )

                    if not created:
                        # UserBook already exists - UPDATE it instead of skipping
                        user_book.status = book_status

                    # Parse rating (convert Goodreads 5-star to our 10-star system)
                    rating_str = row.get('My Rating', '').strip()
                    if rating_str and rating_str != '0':
                        try:
                            user_book.rating = float(rating_str) * 2  # Convert 5★ to 10★
                        except ValueError:
                            pass

                    # Parse dates
                    date_read_str = row.get('Date Read', '').strip()
                    date_added_str = row.get('Date Added', '').strip()

                    from django.utils import timezone

                    # Parse Date Read
                    if date_read_str:
                        try:
                            user_book.finished_at = datetime.strptime(date_read_str, '%Y/%m/%d').date()
                        except ValueError:
                            pass

                    # Parse Date Added
                    added_date = None
                    if date_added_str:
                        try:
                            added_date = datetime.strptime(date_added_str, '%Y/%m/%d').date()
                            # Set created_at to match Goodreads date (not current time)
                            user_book.created_at = timezone.make_aware(datetime.combine(added_date, datetime.min.time()))
                        except ValueError:
                            pass

                    # For "read" books without finished_at, use Date Added as fallback
                    if book_status == 'read' and not user_book.finished_at and added_date:
                        user_book.finished_at = added_date

                    # For currently_reading, set started_at
                    if book_status == 'currently_reading' and added_date:
                        user_book.started_at = added_date

                    # Import review and format quotes
                    review_text = row.get('My Review', '').strip()
                    if review_text and book_status == 'read':
                        # Parse and format quotes in review
                        soup = BeautifulSoup(review_text, 'html.parser')

                        # Collect all <i> tags that need to be converted to quotes
                        i_tags_to_process = []
                        for i_tag in soup.find_all('i'):
                            text = i_tag.get_text(strip=True)
                            # Only process <i> tags with substantial text (likely quotes)
                            if len(text) > 30:
                                i_tags_to_process.append(i_tag)

                        # Process each <i> tag
                        for i_tag in i_tags_to_process:
                            # Check if this <i> is already inside a <blockquote>
                            parent_bq = i_tag.find_parent('blockquote')

                            if parent_bq:
                                # Case 1: <blockquote><i>text</i></blockquote>
                                # Remove inner <i> tag, add class and button to blockquote, wrap blockquote in <i>

                                # First, unwrap the inner <i> tag (move its contents up)
                                i_contents = list(i_tag.contents)
                                for content in i_contents:
                                    i_tag.insert_before(content)
                                i_tag.decompose()  # Remove the now-empty <i> tag

                                # Add class to blockquote
                                if 'quote-block' not in parent_bq.get('class', []):
                                    parent_bq['class'] = parent_bq.get('class', []) + ['quote-block']

                                # Add metadata button if not exists
                                if not parent_bq.find('button', class_='quote-metadata-btn'):
                                    btn = soup.new_tag('button', **{
                                        'class': 'quote-metadata-btn',
                                        'contenteditable': 'false'
                                    })
                                    btn.string = '📖'
                                    parent_bq.append(btn)

                                # Wrap entire blockquote in outer <i>
                                # Target structure: <i><blockquote class="quote-block">text<button></button></blockquote></i>
                                grandparent = parent_bq.parent
                                if grandparent.name != 'i':
                                    outer_i = soup.new_tag('i')
                                    parent_bq.wrap(outer_i)

                            else:
                                # Case 2: Standalone <i>text</i> (no blockquote)
                                # Wrap it: <i><blockquote class="quote-block">text<button></button></blockquote></i>

                                # Create blockquote
                                bq = soup.new_tag('blockquote', **{'class': 'quote-block'})

                                # Create button
                                btn = soup.new_tag('button', **{
                                    'class': 'quote-metadata-btn',
                                    'contenteditable': 'false'
                                })
                                btn.string = '📖'

                                # Move i_tag's content to blockquote
                                # Extract contents from <i>
                                contents = list(i_tag.contents)
                                for content in contents:
                                    bq.append(content.extract())

                                # Add button to blockquote
                                bq.append(btn)

                                # Put blockquote back into <i>
                                i_tag.append(bq)

                        user_book.review = str(soup)

                    user_book.save()

                    # Extract quotes from review after saving UserBook
                    if review_text and book_status == 'read':
                        from apps.reading.models import Quote

                        # Parse HTML to extract quotes
                        soup = BeautifulSoup(review_text, 'html.parser')

                        # Extract from <blockquote> tags
                        blockquotes = soup.find_all('blockquote')
                        for bq in blockquotes:
                            # Check if blockquote contains <i> tag (avoid duplicates)
                            i_tag = bq.find('i')
                            if i_tag:
                                # Use text from <i> tag inside blockquote
                                quote_text = i_tag.get_text(strip=True)
                            else:
                                # Use text directly from blockquote
                                quote_text = bq.get_text(strip=True)

                            if quote_text and len(quote_text) > 30:  # Ignore short quotes (min 30 chars)
                                Quote.objects.create(
                                    user=request.user,
                                    book=book,
                                    user_book=user_book,
                                    book_title=book.title,
                                    book_author=', '.join([a.name for a in book.authors.all()]),
                                    text=quote_text,
                                    is_public=False
                                )

                        # Also extract standalone <i> tags that are NOT inside blockquote
                        # (to catch quotes like <i>"text"</i> without blockquote wrapper)
                        all_i_tags = soup.find_all('i')
                        for i_tag in all_i_tags:
                            # Skip if inside blockquote (already processed above)
                            if i_tag.find_parent('blockquote'):
                                continue

                            quote_text = i_tag.get_text(strip=True)
                            if quote_text and len(quote_text) > 30:  # Ignore short quotes (min 30 chars)
                                Quote.objects.create(
                                    user=request.user,
                                    book=book,
                                    user_book=user_book,
                                    book_title=book.title,
                                    book_author=', '.join([a.name for a in book.authors.all()]),
                                    text=quote_text,
                                    is_public=False
                                )

                    if created:
                        updated_books.append(book.id)

                    imported_count += 1

                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'title': row.get('Title', 'Unknown'),
                        'error': str(e)
                    })
                    skipped_count += 1

            # Reconnect the signal
            post_save.connect(social_signals.create_userbook_feed_item, sender=UserBook)

            # Create feed items only for the most recent 10 finished books
            from apps.social.models import FeedItem, Friendship
            recent_finished_books = UserBook.objects.filter(
                user=request.user,
                status='read',
                finished_at__isnull=False
            ).order_by('-finished_at')[:10]

            # Get followers
            followers = Friendship.objects.filter(
                to_user=request.user,
                status='accepted'
            ).values_list('from_user', flat=True)

            feed_items_to_create = []
            for user_book in recent_finished_books:
                # Check if feed item already exists
                existing = FeedItem.objects.filter(
                    actor=request.user,
                    content_type='UserBook',
                    object_id=user_book.id,
                    feed_type='book_finished'
                ).exists()

                if not existing:
                    preview_text = f'finished reading {user_book.book.title}'
                    if user_book.rating:
                        preview_text += f' and rated it {user_book.rating}/10'

                    # Add feed item for the user themselves
                    feed_items_to_create.append(FeedItem(
                        user=request.user,
                        actor=request.user,
                        feed_type='book_finished',
                        content_type='UserBook',
                        object_id=user_book.id,
                        preview_text=preview_text,
                        preview_image=user_book.book.cover_image if user_book.book.cover_image else '',
                    ))

                    # Add feed item for each follower
                    for follower_id in followers:
                        feed_items_to_create.append(FeedItem(
                            user_id=follower_id,
                            actor=request.user,
                            feed_type='book_finished',
                            content_type='UserBook',
                            object_id=user_book.id,
                            preview_text=preview_text,
                            preview_image=user_book.book.cover_image if user_book.book.cover_image else '',
                        ))

            if feed_items_to_create:
                FeedItem.objects.bulk_create(feed_items_to_create)

            return Response({
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count,
                'created_books': len(created_books),
                'updated_books': len(updated_books),
                'feed_items_created': len(feed_items_to_create),
                'errors': errors[:10]  # Return first 10 errors
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Reconnect signal in case of error
            post_save.connect(social_signals.create_userbook_feed_item, sender=UserBook)

            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Failed to process CSV: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

