from rest_framework import serializers
from apps.books.models import Book, BookDNA, BookDNAVote
from apps.books.serializers import BookListSerializer
from .survey import SURVEY_QUESTIONS, THEME_OPTIONS, VALID_THEME_IDS, VALID_GENRE_TAG_IDS


class BookDNASerializer(serializers.ModelSerializer):
    """Serializer for BookDNA model."""

    class Meta:
        model = BookDNA
        fields = [
            'id', 'pace', 'complexity', 'emotional_intensity',
            'darkness', 'character_focus', 'introspection',
            'themes', 'primary_themes', 'genre_tags', 'primary_genre_tag',
            'source', 'vote_count', 'confidence_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookDNAVoteSerializer(serializers.ModelSerializer):
    """Serializer for BookDNAVote model."""

    class Meta:
        model = BookDNAVote
        fields = [
            'id', 'book', 'user_book',
            'pace', 'complexity', 'emotional_intensity',
            'darkness', 'character_focus', 'introspection',
            'themes', 'primary_themes', 'genre_tags', 'primary_genre_tag', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SurveySubmitSerializer(serializers.Serializer):
    """Serializer for survey submission."""
    book_id = serializers.IntegerField()
    user_book_id = serializers.IntegerField(required=False, allow_null=True)
    responses = serializers.DictField(child=serializers.FloatField(min_value=0, max_value=1))
    themes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    primary_themes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    genre_tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    primary_genre_tag = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    def validate_responses(self, value):
        """Validate that responses contain valid attribute keys."""
        valid_keys = {'pace', 'complexity', 'emotional_intensity', 'darkness', 'character_focus', 'introspection'}
        for key in value.keys():
            if key not in valid_keys:
                raise serializers.ValidationError(f"Invalid attribute key: {key}")
        return value

    def validate_themes(self, value):
        """Validate theme IDs."""
        for theme in value:
            if theme not in VALID_THEME_IDS:
                raise serializers.ValidationError(f"Invalid theme: {theme}")
        return value

    def validate_primary_themes(self, value):
        """Validate primary themes (max 3, must be valid theme IDs)."""
        if len(value) > 3:
            raise serializers.ValidationError("Maximum 3 primary themes allowed")
        for theme in value:
            if theme not in VALID_THEME_IDS:
                raise serializers.ValidationError(f"Invalid primary theme: {theme}")
        return value

    def validate_genre_tags(self, value):
        """Validate genre tag IDs."""
        for tag in value:
            if tag not in VALID_GENRE_TAG_IDS:
                raise serializers.ValidationError(f"Invalid genre tag: {tag}")
        return value

    def validate_primary_genre_tag(self, value):
        """Validate primary genre tag."""
        if value and value not in VALID_GENRE_TAG_IDS:
            raise serializers.ValidationError(f"Invalid primary genre tag: {value}")
        return value

    def validate(self, data):
        """Ensure primary_themes is a subset of themes, primary_genre_tag is in genre_tags."""
        primary = set(data.get('primary_themes', []))
        themes = set(data.get('themes', []))
        if primary and not primary.issubset(themes):
            raise serializers.ValidationError("Primary themes must also be in the themes list")
        pgt = data.get('primary_genre_tag')
        genre_tags = data.get('genre_tags', [])
        if pgt and genre_tags and pgt not in genre_tags:
            raise serializers.ValidationError("Primary genre tag must also be in the genre_tags list")
        return data


class RecommendedBookSerializer(serializers.Serializer):
    """Serializer for recommended books."""
    book = BookListSerializer()
    match_score = serializers.FloatField()
    reason = serializers.CharField(required=False)
    context = serializers.CharField(required=False)


class TasteProfileSerializer(serializers.Serializer):
    """Serializer for user taste profile."""
    pace_preference = serializers.FloatField()
    complexity_tolerance = serializers.FloatField()
    emotional_preference = serializers.FloatField()
    darkness_tolerance = serializers.FloatField()
    character_focus_preference = serializers.FloatField()
    introspection_preference = serializers.FloatField()
    themes_affinity = serializers.ListField(child=serializers.CharField())
    books_completed = serializers.IntegerField()
    books_abandoned = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    vote_count = serializers.IntegerField()
    last_updated = serializers.CharField(allow_null=True)


class SurveyConfigSerializer(serializers.Serializer):
    """Serializer for survey configuration."""
    questions = serializers.ListField()
    theme_options = serializers.ListField()
