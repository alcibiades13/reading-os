from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg

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
