from rest_framework import serializers
from apps.reading.models import UserBook, Quote, QuoteTag
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

    class Meta:
        model = Quote
        fields = [
            'id',
            'book',
            'book_title',
            'book_author',
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
            'rating',
            'review',
            'is_favorite',
            'current_page',
            'reading_progress',
            'quotes_count',
            'depth_score',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'quotes_count', 'depth_score', 'updated_at']

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
        status = data.get('status')
        started_at = data.get('started_at')
        finished_at = data.get('finished_at')
        
        # Validate finished books have finished_at date
        if status == 'read' and not finished_at:
            raise serializers.ValidationError(
                "Finished books must have a finished_at date"
            )
        
        # Validate currently reading books have started_at date
        if status == 'currently_reading' and not started_at:
            raise serializers.ValidationError(
                "Currently reading books must have a started_at date"
            )
        
        # Validate date order
        if started_at and finished_at and started_at > finished_at:
            raise serializers.ValidationError(
                "Started date cannot be after finished date"
            )
        
        return data

