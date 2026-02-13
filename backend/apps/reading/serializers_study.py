from rest_framework import serializers
from apps.reading.models_study import StudyNote
from apps.reading.models import QuoteTag, Quote
from apps.books.serializers import BookListSerializer


class StudyNoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for study note lists"""
    tags = serializers.StringRelatedField(many=True, read_only=True)
    book_title = serializers.CharField(read_only=True)
    book_author = serializers.CharField(read_only=True)
    references_list = serializers.ListField(read_only=True)

    class Meta:
        model = StudyNote
        fields = [
            'id',
            'book',
            'book_title',
            'book_author',
            'reference',
            'references_list',
            'note_type',
            'content',
            'page_number',
            'chapter',
            'highlights',
            'tags',
            'is_promoted_to_quote',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class StudyNoteDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single study note view"""
    book = BookListSerializer(read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)

    # For write operations
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = StudyNote
        fields = [
            'id',
            'user',
            'book',
            'user_book',
            'reference',
            'note_type',
            'content',
            'page_number',
            'chapter',
            'highlights',
            'tags',
            'tag_ids',
            'is_promoted_to_quote',
            'promoted_quote',
            'is_public',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'promoted_quote', 'created_at', 'updated_at']


class StudyNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating study notes"""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )
    chapter = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    page_number = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = StudyNote
        fields = [
            'book',
            'user_book',
            'reference',
            'note_type',
            'content',
            'page_number',
            'chapter',
            'tag_ids',
            'is_public',
        ]

    def create(self, validated_data):
        """Handle many-to-many relationships"""
        tags = validated_data.pop('tags', [])
        study_note = StudyNote.objects.create(**validated_data)

        if tags:
            study_note.tags.set(tags)

        return study_note


class StudyNoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating study notes"""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=QuoteTag.objects.all(),
        source='tags',
        required=False
    )

    class Meta:
        model = StudyNote
        fields = [
            'id',
            'reference',
            'note_type',
            'content',
            'page_number',
            'chapter',
            'highlights',
            'tag_ids',
            'is_public',
        ]
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        """Handle many-to-many relationships"""
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags is not None:
            instance.tags.set(tags)

        instance.save()
        return instance
