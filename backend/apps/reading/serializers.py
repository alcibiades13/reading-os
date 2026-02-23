from rest_framework import serializers
from apps.reading.models import UserBook, Quote, QuoteTag, VocabularyWord
from apps.books.serializers import BookListSerializer
from apps.users.serializers import UserSerializer


class QuoteTagSerializer(serializers.ModelSerializer):
    """Serializer for QuoteTag model"""
    
    class Meta:
        model = QuoteTag
        fields = [
            'id',
            'name',
            'slug',
            'color',
            'is_ai_suggested',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'user', 'created_at']


class QuoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for quote lists"""
    tags = QuoteTagSerializer(many=True, read_only=True)
    book_cover = serializers.SerializerMethodField()
    book_slug = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            'id',
            'book',
            'book_title',
            'book_author',
            'book_cover',
            'book_slug',
            'text',
            'page_number',
            'chapter',
            'note',
            'tags',
            'is_favorite',
            'is_public',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'user_book', 'created_at']

    def get_book_slug(self, obj):
        """Get book slug from related book"""
        if obj.book:
            return obj.book.slug
        return ''

    def get_book_cover(self, obj):
        """Get book cover URL from related book"""
        try:
            if obj.book:
                # Book exists, check for cover_image field
                if hasattr(obj.book, 'cover_image') and obj.book.cover_image:
                    return obj.book.cover_image
            # No book linked or no cover
            return None
        except Exception as e:
            print(f"Error getting book cover for quote {obj.id}: {e}")
            return None


class QuoteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single quote view"""
    book = BookListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    tags = QuoteTagSerializer(many=True, read_only=True)
    
    # For write operations
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )
    
    class Meta:
        model = Quote
        fields = [
            'id',
            'user',
            'book',
            'user_book',
            'text',
            'page_number',
            'chapter',
            'note',
            'tags',
            'tag_ids',
            'is_favorite',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class QuoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quotes"""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = Quote
        fields = [
            'book',
            'user_book',
            'book_title',
            'book_author',
            'text',
            'page_number',
            'chapter',
            'note',
            'tag_ids',
            'is_favorite',
            'is_public',
        ]
    
    def validate(self, data):
        """Validate that user_book belongs to the book"""
        user_book = data.get('user_book')
        book = data.get('book')
        
        if user_book and book:
            if user_book.book_id != book.id:
                raise serializers.ValidationError(
                    "UserBook must belong to the specified book"
                )
        
        return data
    
    def create(self, validated_data):
        """Handle many-to-many relationships"""
        tags = validated_data.pop('tags', [])
        quote = Quote.objects.create(**validated_data)
        
        if tags:
            quote.tags.set(tags)
        
        return quote


class UserBookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user book lists"""
    book = BookListSerializer(read_only=True)
    reading_progress = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserBook
        fields = [
            'id',
            'book',
            'status',
            'started_at',
            'finished_at',
            'rating',
            'review',
            'is_favorite',
            'current_page',
            'reading_progress',
            'is_owned',
            'is_wishlisted',
            'quotes_count',
            'depth_score',
            'updated_at',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'quotes_count', 'depth_score', 'updated_at', 'created_at']

    def validate_rating(self, value):
        """Ensure rating is properly converted to Decimal"""
        if value is not None:
            from decimal import Decimal
            return Decimal(str(value))
        return value


class UserBookDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single user book view"""
    book = BookListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    reading_progress = serializers.IntegerField(read_only=True)
    quotes = QuoteListSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserBook
        fields = [
            'id',
            'user',
            'book',
            'status',
            'started_at',
            'finished_at',
            'current_page',
            'rating',
            'review',
            'is_favorite',
            'quotes_count',
            'depth_score',
            'reading_progress',
            'is_owned',
            'is_wishlisted',
            'is_public',
            'quotes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'quotes_count',
            'depth_score',
            'created_at',
            'updated_at',
        ]


class QuoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating quotes"""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = Quote
        fields = [
            'text',
            'book_title',
            'book_author',
            'book',
            'user_book',
            'page_number',
            'chapter',
            'note',
            'tag_ids',
            'is_favorite',
            'is_public',
        ]

    def update(self, instance, validated_data):
        """Handle many-to-many relationships"""
        tags = validated_data.pop('tags', None)

        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags is not None:
            instance.tags.set(tags)

        return instance


class UserBookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user books"""

    class Meta:
        model = UserBook
        fields = [
            'id',
            'book',
            'status',
            'started_at',
            'finished_at',
            'current_page',
            'rating',
            'review',
            'is_favorite',
            'is_owned',
            'is_wishlisted',
            'is_public',
        ]
        read_only_fields = ['id']

    def validate_rating(self, value):
        """Ensure rating is properly converted to Decimal"""
        if value is not None:
            from decimal import Decimal
            # Convert to Decimal to preserve precision
            return Decimal(str(value))
        return value

    def validate(self, data):
        """Validate reading dates and status"""
        from django.utils import timezone

        status = data.get('status')
        started_at = data.get('started_at')
        finished_at = data.get('finished_at')

        # Auto-set finished_at if status is 'read' and finished_at not provided
        if status == 'read' and not finished_at:
            data['finished_at'] = timezone.now().date()

        # Auto-set started_at if status is 'currently_reading' and started_at not provided
        if status == 'currently_reading' and not started_at:
            data['started_at'] = timezone.now().date()
        
        # Validate date order
        if started_at and finished_at and started_at > finished_at:
            raise serializers.ValidationError(
                "Started date cannot be after finished date"
            )
        
        return data


class VocabularyWordSerializer(serializers.ModelSerializer):
    """Serializer for vocabulary words"""

    class Meta:
        model = VocabularyWord
        fields = [
            'id',
            'word',
            'definition',
            'context',
            'book',
            'book_title',
            'book_author',
            'page_number',
            'mastery',
            'review_count',
            'last_reviewed_at',
            'tags',
            'is_favorite',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


