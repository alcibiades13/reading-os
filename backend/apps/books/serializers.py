from django.utils.text import slugify
from rest_framework import serializers
from apps.books.models import Author, Publisher, Genre, Tag, Book


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for Author model"""
    books_count = serializers.SerializerMethodField()
    author_group_id = serializers.IntegerField(
        source='author_group.id', read_only=True, allow_null=True
    )
    aliases = serializers.SerializerMethodField()
    similar_authors = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'slug',
            'bio',
            'birth_date',
            'death_date',
            'photo',
            'books_count',
            'author_group_id',
            'is_primary_alias',
            'aliases',
            'similar_authors',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_books_count(self, obj):
        """Count books by this author (across all aliases if grouped)"""
        if obj.author_group_id:
            alias_ids = obj.author_group.members.values_list('id', flat=True)
            return Book.objects.filter(authors__id__in=alias_ids).distinct().count()
        return obj.books.count()

    def get_aliases(self, obj):
        """Return other name spellings for this author."""
        if not obj.author_group_id:
            return []
        return [{
            'id': a.id, 'name': a.name, 'slug': a.slug,
            'photo': a.photo, 'is_primary': a.is_primary_alias,
        } for a in obj.author_group.members.exclude(id=obj.id)]

    def get_similar_authors(self, obj):
        """Compute similar authors based on shared DNA themes."""
        # Only compute for detail views, not lists
        request = self.context.get('request')
        view = self.context.get('view')
        if view and hasattr(view, 'action') and view.action != 'retrieve':
            return []
        from apps.books.utils import compute_similar_authors
        return compute_similar_authors(obj)

    def to_representation(self, instance):
        """
        For grouped authors, use the canonical (primary) author's bio/photo/dates
        so every alias page shows the same correct data.
        """
        data = super().to_representation(instance)

        if not instance.author_group_id:
            return data

        # Find the best source within the group (primary first, then any sibling)
        primary = (
            instance.author_group.members
            .filter(is_primary_alias=True)
            .first()
        )
        # Ordered preference: primary, then siblings with data, then self
        sources = []
        if primary and primary.id != instance.id:
            sources.append(primary)
        for sib in instance.author_group.members.exclude(id=instance.id).order_by('-is_primary_alias'):
            if sib.id != (primary.id if primary else None):
                sources.append(sib)

        for field in ('bio', 'photo', 'birth_date', 'death_date'):
            if not data.get(field):
                for src in sources:
                    val = getattr(src, field, None)
                    if val:
                        data[field] = str(val) if field in ('birth_date', 'death_date') else val
                        break

        return data


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
    book_group_id = serializers.IntegerField(source='book_group.id', read_only=True, allow_null=True)

    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'slug',
            'subtitle',
            'authors',
            'publisher_name',
            'published_date',
            'language',
            'pages',
            'cover_image',
            'book_group_id',
        ]
        read_only_fields = ['id', 'slug']


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

    # Accept flexible date formats (YYYY, YYYY-MM, YYYY-MM-DD)
    published_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Add support for updating authors/publisher by name (not just IDs)
    publisher_name = serializers.CharField(
        max_length=200,
        write_only=True,
        required=False,
        allow_blank=True
    )

    # Edition/Version information
    book_group_id = serializers.IntegerField(source='book_group.id', read_only=True, allow_null=True)
    has_other_editions = serializers.SerializerMethodField()
    other_editions = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'slug',
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
            'book_group_id',
            'has_other_editions',
            'other_editions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_has_other_editions(self, obj):
        """Check if this book has other editions"""
        return obj.has_other_editions()

    def get_other_editions(self, obj):
        """Get list of other editions"""
        if not obj.book_group:
            return []

        other_editions = obj.get_other_editions()
        return [{
            'id': ed.id,
            'title': ed.title,
            'subtitle': ed.subtitle,
            'language': ed.language,
            'publisher': ed.publisher.name if ed.publisher else None,
            'published_date': ed.published_date,
            'pages': ed.pages,
            'isbn': ed.isbn,
            'cover_image': ed.cover_image,
            'is_primary': ed.is_primary_edition,
        } for ed in other_editions]

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

    def validate_isbn(self, value):
        """Convert empty ISBN to None to avoid unique constraint violation"""
        return value or None

    def validate_published_date(self, value):
        """Accept year-only (YYYY) or year-month (YYYY-MM) formats"""
        if value is None or value == '':
            return None
        import datetime
        # If it's already a date object, return as-is
        if isinstance(value, datetime.date):
            return value
        val = str(value).strip()
        if not val:
            return None
        # Year only: "2006"
        if len(val) == 4 and val.isdigit():
            return datetime.date(int(val), 1, 1)
        # Year-month: "2006-01"
        if len(val) == 7 and val[4] == '-':
            return datetime.date(int(val[:4]), int(val[5:7]), 1)
        # Full date: "2006-01-15"
        try:
            return datetime.date.fromisoformat(val)
        except ValueError:
            raise serializers.ValidationError(f"Invalid date format: {val}. Use YYYY, YYYY-MM, or YYYY-MM-DD.")

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

        # Handle genres — match by slug to avoid case-based duplicates
        if genre_names:
            genre_objs = []
            for genre_name in genre_names:
                genre_name_clean = genre_name.strip() if genre_name else ''
                if genre_name_clean:
                    slug = slugify(genre_name_clean)[:50]
                    if slug:
                        genre, _ = Genre.objects.get_or_create(
                            slug=slug,
                            defaults={'name': genre_name_clean.lower(), 'description': ''}
                        )
                        genre_objs.append(genre)
            book.genres.set(genre_objs)

        return book


