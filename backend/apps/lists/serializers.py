from rest_framework import serializers
from apps.lists.models import ReadingList, ReadingListItem
from apps.books.serializers import BookListSerializer


class ReadingListItemSerializer(serializers.ModelSerializer):
    """Serializer for ReadingListItem"""
    book = BookListSerializer(read_only=True)
    
    class Meta:
        model = ReadingListItem
        fields = [
            'id',
            'book',
            'order',
            'note',
            'added_at',
        ]
        read_only_fields = ['id', 'reading_list', 'added_at']


class ReadingListListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for reading list lists"""
    books_count = serializers.IntegerField(source='books_count', read_only=True)
    
    class Meta:
        model = ReadingList
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'is_smart',
            'is_public',
            'books_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'user', 'created_at', 'updated_at']


class ReadingListDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single reading list view"""
    items = ReadingListItemSerializer(many=True, read_only=True)
    books_count = serializers.IntegerField(source='books_count', read_only=True)
    
    class Meta:
        model = ReadingList
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'is_smart',
            'filter_rules',
            'is_public',
            'books_count',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'user', 'created_at', 'updated_at']


class ReadingListCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reading lists"""
    
    class Meta:
        model = ReadingList
        fields = [
            'title',
            'description',
            'is_smart',
            'filter_rules',
            'is_public',
        ]
    
    def validate_filter_rules(self, value):
        """Validate filter_rules if is_smart is True"""
        if self.initial_data.get('is_smart') and not value:
            raise serializers.ValidationError(
                "Smart lists must have filter_rules defined"
            )
        return value


class ReadingListItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding books to reading lists"""
    
    class Meta:
        model = ReadingListItem
        fields = [
            'reading_list',
            'book',
            'order',
            'note',
        ]
    
    def validate(self, data):
        """Validate that book is not already in the list"""
        reading_list = data.get('reading_list')
        book = data.get('book')
        
        if ReadingListItem.objects.filter(
            reading_list=reading_list,
            book=book
        ).exists():
            raise serializers.ValidationError(
                "This book is already in the list"
            )
        
        return data

