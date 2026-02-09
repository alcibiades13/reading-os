from rest_framework import serializers
from apps.codex.models import JournalEntry, Manuscript, Chapter


class JournalEntrySerializer(serializers.ModelSerializer):
    """Serializer for JournalEntry model"""
    word_count = serializers.ReadOnlyField()

    class Meta:
        model = JournalEntry
        fields = [
            'id',
            'title',
            'content',
            'mood',
            'tags',
            'is_locked',
            'book',
            'word_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'word_count', 'created_at', 'updated_at']


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for Chapter model"""
    word_count = serializers.ReadOnlyField()

    class Meta:
        model = Chapter
        fields = [
            'id',
            'title',
            'content',
            'order',
            'word_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'word_count', 'created_at', 'updated_at']


class ManuscriptListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for manuscript lists"""
    current_word_count = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()
    chapter_count = serializers.SerializerMethodField()

    class Meta:
        model = Manuscript
        fields = [
            'id',
            'title',
            'subtitle',
            'genre',
            'cover_color',
            'target_word_count',
            'current_word_count',
            'completion_percentage',
            'chapter_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'current_word_count', 'completion_percentage', 'chapter_count', 'created_at', 'updated_at']

    def get_chapter_count(self, obj):
        return obj.chapters.count()


class ManuscriptDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with chapters for single manuscript view"""
    chapters = ChapterSerializer(many=True, read_only=True)
    current_word_count = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Manuscript
        fields = [
            'id',
            'title',
            'subtitle',
            'genre',
            'cover_color',
            'target_word_count',
            'current_word_count',
            'completion_percentage',
            'chapters',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'current_word_count', 'completion_percentage', 'created_at', 'updated_at']


class ManuscriptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating manuscripts with optional initial chapter"""

    class Meta:
        model = Manuscript
        fields = [
            'id',
            'title',
            'subtitle',
            'genre',
            'cover_color',
            'target_word_count',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        manuscript = Manuscript.objects.create(**validated_data)
        # Create initial chapter
        Chapter.objects.create(
            manuscript=manuscript,
            title='Chapter 1',
            order=1
        )
        return manuscript
