from rest_framework import serializers
from apps.challenges.models import ReadingChallenge
from apps.books.serializers import GenreSerializer, TagSerializer
from apps.books.models import Genre, Tag


class ReadingChallengeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for challenge lists"""
    progress_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ReadingChallenge
        fields = [
            'id',
            'title',
            'target_books',
            'completed_books',
            'progress_percentage',
            'is_completed',
            'start_date',
            'end_date',
            'is_active',
            'is_public',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'completed_books', 'created_at']


class ReadingChallengeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single challenge view"""
    progress_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    genre_filter = GenreSerializer(many=True, read_only=True)
    tag_filter = TagSerializer(many=True, read_only=True)
    
    # IDs for write operations
    genre_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Genre.objects.all(),
        source='genre_filter',
        required=False
    )
    tag_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        source='tag_filter',
        required=False
    )
    
    class Meta:
        model = ReadingChallenge
        fields = [
            'id',
            'title',
            'description',
            'target_books',
            'completed_books',
            'progress_percentage',
            'is_completed',
            'start_date',
            'end_date',
            'genre_filter',
            'genre_filter_ids',
            'tag_filter',
            'tag_filter_ids',
            'min_pages',
            'is_active',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'completed_books', 'created_at', 'updated_at']


class ReadingChallengeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating challenges"""
    genre_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        source='genre_filter',
        required=False
    )
    tag_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tag_filter',
        required=False
    )
    
    class Meta:
        model = ReadingChallenge
        fields = [
            'title',
            'description',
            'target_books',
            'start_date',
            'end_date',
            'genre_filter_ids',
            'tag_filter_ids',
            'min_pages',
            'is_active',
            'is_public',
        ]
    
    def validate(self, data):
        """Validate challenge dates and targets"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        target_books = data.get('target_books')
        
        # Validate date order
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                "Start date must be before end date"
            )
        
        # Validate target is reasonable
        if target_books and target_books < 1:
            raise serializers.ValidationError(
                "Target must be at least 1 book"
            )
        
        if target_books and target_books > 1000:
            raise serializers.ValidationError(
                "Target cannot exceed 1000 books"
            )
        
        return data
    
    def create(self, validated_data):
        """Handle many-to-many relationships"""
        genre_filter = validated_data.pop('genre_filter', [])
        tag_filter = validated_data.pop('tag_filter', [])
        
        challenge = ReadingChallenge.objects.create(**validated_data)
        
        if genre_filter:
            challenge.genre_filter.set(genre_filter)
        if tag_filter:
            challenge.tag_filter.set(tag_filter)
        
        return challenge


class ReadingChallengeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating challenges"""
    genre_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        source='genre_filter',
        required=False
    )
    tag_filter_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        source='tag_filter',
        required=False
    )
    
    class Meta:
        model = ReadingChallenge
        fields = [
            'title',
            'description',
            'target_books',
            'start_date',
            'end_date',
            'genre_filter_ids',
            'tag_filter_ids',
            'min_pages',
            'is_active',
            'is_public',
        ]
    
    def update(self, instance, validated_data):
        """Handle many-to-many relationships"""
        genre_filter = validated_data.pop('genre_filter', None)
        tag_filter = validated_data.pop('tag_filter', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many fields
        if genre_filter is not None:
            instance.genre_filter.set(genre_filter)
        if tag_filter is not None:
            instance.tag_filter.set(tag_filter)
        
        # Recalculate progress
        instance.update_progress()
        
        return instance

