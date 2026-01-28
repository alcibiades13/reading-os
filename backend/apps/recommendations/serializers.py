from rest_framework import serializers
from apps.books.models import Book, BookDNA, BookDNAVote
from apps.books.serializers import BookListSerializer
from .survey import SURVEY_QUESTIONS, THEME_OPTIONS


class BookDNASerializer(serializers.ModelSerializer):
    """Serializer for BookDNA model."""

    class Meta:
        model = BookDNA
        fields = [
            'id', 'pace', 'complexity', 'emotional_intensity',
            'darkness', 'character_focus', 'introspection',
            'themes', 'source', 'vote_count', 'confidence_score',
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
            'themes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SurveySubmitSerializer(serializers.Serializer):
    """Serializer for survey submission."""
    book_id = serializers.IntegerField()
    user_book_id = serializers.IntegerField(required=False, allow_null=True)
    responses = serializers.DictField(child=serializers.FloatField(min_value=0, max_value=1))
    themes = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_responses(self, value):
        """Validate that responses contain valid attribute keys."""
        valid_keys = {'pace', 'complexity', 'emotional_intensity', 'darkness', 'character_focus', 'introspection'}
        for key in value.keys():
            if key not in valid_keys:
                raise serializers.ValidationError(f"Invalid attribute key: {key}")
        return value

    def validate_themes(self, value):
        """Validate theme IDs."""
        valid_themes = {t['id'] for t in THEME_OPTIONS}
        for theme in value:
            if theme not in valid_themes:
                raise serializers.ValidationError(f"Invalid theme: {theme}")
        return value


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
