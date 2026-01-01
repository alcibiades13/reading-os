from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count

from apps.books.models import Author, Publisher, Genre, Tag, Book
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


class AuthorViewSet(viewsets.ModelViewSet):
    """ViewSet for Author model"""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'bio']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get all books by this author"""
        author = self.get_object()
        books = author.books.all()
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)


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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle', 'isbn', 'authors__name', 'description']
    ordering_fields = ['title', 'published_date', 'created_at', 'pages']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return BookCreateSerializer
        elif self.action == 'retrieve':
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
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular books (most readers)"""
        books = Book.objects.annotate(
            readers_count=Count('user_books')
        ).filter(
            readers_count__gt=0
        ).order_by('-readers_count')[:20]
        
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added books"""
        books = Book.objects.all().order_by('-created_at')[:20]
        serializer = BookListSerializer(books, many=True)
        return Response(serializer.data)

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
