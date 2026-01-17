from rest_framework import serializers
from apps.books.models import Author, Publisher, Genre, Tag, Book


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model"""
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'bio',
            'birth_date',
            'death_date',
            'photo',
            'books_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_books_count(self, obj):
        """Count books by this author"""
        return obj.books.count()


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for Publisher model"""
    
    class Meta:
        model = Publisher
        fields = [
            'id',
            'name',
            'country',
            'website',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subgenres = serializers.SerializerMethodField()
    
    class Meta:
        model = Genre
        fields = [
            'id',
            'name',
            'slug',
            'parent',
            'parent_name',
            'description',
            'subgenres',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_subgenres(self, obj):
        """Get child genres"""
        if obj.subgenres.exists():
            return GenreSerializer(obj.subgenres.all(), many=True).data
        return []


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    
    class Meta:
        model = Tag
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'description',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book lists"""
    authors = AuthorSerializer(many=True, read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'subtitle',
            'authors',
            'publisher_name',
            'published_date',
            'language',
            'pages',
            'cover_image',
        ]
        read_only_fields = ['id']


class BookDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single book view"""
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    # IDs for write operations
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Author.objects.all(),
        required=False
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Genre.objects.all(),
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        required=False
    )

    # Add support for updating authors/publisher by name (not just IDs)
    publisher_name = serializers.CharField(
        max_length=200,
        write_only=True,
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'subtitle',
            'description',
            'authors',
            'author_ids',
            'publisher',
            'publisher_name',
            'published_date',
            'language',
            'pages',
            'cover_image',
            'genres',
            'genre_ids',
            'tags',
            'tag_ids',
            'source',
            'external_ids',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        """Handle 'authors' array of strings from frontend"""
        # If 'authors' is sent as array of strings (names), convert to author_ids
        if 'authors' in data and isinstance(data.get('authors'), list):
            authors_input = data.pop('authors')
            if authors_input and isinstance(authors_input[0], str):
                # It's author names - create or get authors and convert to IDs
                author_ids = []
                for author_name in authors_input:
                    if author_name.strip():
                        author, _ = Author.objects.get_or_create(
                            name=author_name.strip(),
                            defaults={'bio': ''}
                        )
                        author_ids.append(author.id)
                data['author_ids'] = author_ids

        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        """Handle update with support for author names and publisher name"""
        # Handle author_ids (PrimaryKeyRelatedField)
        if 'author_ids' in validated_data:
            author_objs = validated_data.pop('author_ids')
            instance.authors.set(author_objs)

        # Handle publisher by name if provided
        publisher_name = validated_data.pop('publisher_name', None)
        if publisher_name:
            publisher_obj, _ = Publisher.objects.get_or_create(
                name=publisher_name.strip(),
                defaults={'country': ''}
            )
            instance.publisher = publisher_obj

        # Handle genre_ids if provided
        if 'genre_ids' in validated_data:
            instance.genres.set(validated_data.pop('genre_ids'))

        # Handle tag_ids if provided
        if 'tag_ids' in validated_data:
            instance.tags.set(validated_data.pop('tag_ids'))

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating books"""
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        source='authors'
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        source='genres',
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = Book
        fields = [
            'isbn',
            'title',
            'subtitle',
            'description',
            'author_ids',
            'publisher',
            'published_date',
            'language',
            'pages',
            'cover_image',
            'genre_ids',
            'tag_ids',
            'source',
            'external_ids',
        ]

    def create(self, validated_data):
        """Handle many-to-many relationships"""
        authors = validated_data.pop('authors', [])
        genres = validated_data.pop('genres', [])
        tags = validated_data.pop('tags', [])

        book = Book.objects.create(**validated_data)

        if authors:
            book.authors.set(authors)
        if genres:
            book.genres.set(genres)
        if tags:
            book.tags.set(tags)

        return book


class BookImportSerializer(serializers.Serializer):
    """Serializer for importing books from external sources (Google Books, etc)"""
    title = serializers.CharField(max_length=500)
    subtitle = serializers.CharField(max_length=500, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    isbn_13 = serializers.CharField(max_length=13, required=False, allow_null=True, allow_blank=True)
    isbn_10 = serializers.CharField(max_length=10, required=False, allow_null=True, allow_blank=True)
    cover_image_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    published_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    page_count = serializers.IntegerField(required=False, allow_null=True)
    language = serializers.CharField(max_length=10, required=False, default='en')

    # External source data
    google_books_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    open_library_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    delfi_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source = serializers.CharField(default='google_books')

    # Related data as strings/lists (will be created if they don't exist)
    authors = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True
    )
    publisher_name = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    genres = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )

    def create(self, validated_data):
        """Create book and related objects"""
        # Extract related data
        author_names = validated_data.pop('authors', [])
        publisher_name = validated_data.pop('publisher_name', None)
        genre_names = validated_data.pop('genres', [])

        # Use ISBN-13 as primary ISBN, fallback to ISBN-10
        isbn = validated_data.pop('isbn_13', None) or validated_data.pop('isbn_10', None)

        # Prepare external_ids JSON
        external_ids = {}
        if validated_data.get('google_books_id'):
            external_ids['google_books_id'] = validated_data.pop('google_books_id')
        if validated_data.get('open_library_id'):
            external_ids['open_library_id'] = validated_data.pop('open_library_id')
        if validated_data.get('delfi_id'):
            external_ids['delfi_id'] = validated_data.pop('delfi_id')

        # Parse published_date - handle year-only format (e.g., "1951")
        published_date = validated_data.get('published_date')
        if published_date:
            # If it's just a year (4 digits), convert to YYYY-01-01
            if len(published_date) == 4 and published_date.isdigit():
                published_date = f"{published_date}-01-01"
            # If it's YYYY-MM, add day
            elif len(published_date) == 7 and published_date[4] == '-':
                published_date = f"{published_date}-01"
            # Otherwise keep as is (should be YYYY-MM-DD)

        # Prepare book data
        book_data = {
            'title': validated_data.get('title'),
            'subtitle': validated_data.get('subtitle', ''),
            'description': validated_data.get('description', ''),
            'isbn': isbn,
            'published_date': published_date,
            'pages': validated_data.get('page_count'),
            'language': validated_data.get('language', 'en'),
            'cover_image': validated_data.get('cover_image_url', ''),
            'source': validated_data.get('source', 'google_books'),
            'external_ids': external_ids,
        }

        # Remove None values
        book_data = {k: v for k, v in book_data.items() if v is not None}

        # Handle publisher
        publisher_obj = None
        if publisher_name:
            publisher_obj, _ = Publisher.objects.get_or_create(
                name=publisher_name,
                defaults={'country': ''}
            )
            book_data['publisher'] = publisher_obj

        # Create the book
        book = Book.objects.create(**book_data)

        # Handle authors
        if author_names:
            author_objs = []
            for author_name in author_names:
                author, _ = Author.objects.get_or_create(
                    name=author_name,
                    defaults={'bio': ''}
                )
                author_objs.append(author)
            book.authors.set(author_objs)

        # Handle genres
        if genre_names:
            genre_objs = []
            for genre_name in genre_names:
                # Convert genre name to lowercase for consistency
                genre_name_lower = genre_name.lower() if genre_name else ''
                if genre_name_lower:
                    genre, _ = Genre.objects.get_or_create(
                        name=genre_name_lower,
                        defaults={'description': ''}
                    )
                    genre_objs.append(genre)
            book.genres.set(genre_objs)

        return book


