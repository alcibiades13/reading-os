from rest_framework import serializers

from apps.contributions.models import (
    ContributionLog, UserReputation, Badge, UserBadge, ContributionFlag,
)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['slug', 'name', 'description', 'icon', 'color', 'category']


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'awarded_at']


class ContributionLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ContributionLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'content_type', 'object_id', 'category',
            'base_points', 'awarded_points',
            'quality_status', 'is_reverted',
            'metadata', 'created_at',
        ]

    def get_user_name(self, obj):
        return obj.user.full_name or obj.user.email


class UserReputationSerializer(serializers.ModelSerializer):
    next_tier = serializers.CharField(read_only=True)
    next_tier_points_needed = serializers.IntegerField(read_only=True)
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    badges = serializers.SerializerMethodField()

    class Meta:
        model = UserReputation
        fields = [
            'tier', 'tier_display', 'tier_updated_at', 'is_tier_locked',
            'total_points', 'content_points', 'community_points',
            'curation_points', 'reading_points',
            'total_contributions', 'quality_ratio',
            'approved_count', 'flagged_count', 'rejected_count',
            'next_tier', 'next_tier_points_needed',
            'badges',
        ]

    def get_badges(self, obj):
        earned = UserBadge.objects.filter(user=obj.user).select_related('badge')[:10]
        return UserBadgeSerializer(earned, many=True).data


class PublicUserReputationSerializer(serializers.ModelSerializer):
    """Lightweight reputation for public profiles."""
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    badges = serializers.SerializerMethodField()

    class Meta:
        model = UserReputation
        fields = [
            'tier', 'tier_display', 'total_points', 'total_contributions',
            'badges',
        ]

    def get_badges(self, obj):
        earned = UserBadge.objects.filter(user=obj.user).select_related('badge')[:5]
        return UserBadgeSerializer(earned, many=True).data


class ContributionDashboardSerializer(serializers.Serializer):
    """Serializer for admin contribution dashboard."""
    total_contributions_all_time = serializers.IntegerField()
    total_contributions_this_week = serializers.IntegerField()
    active_contributors_this_week = serializers.IntegerField()
    flagged_pending = serializers.IntegerField()
    average_quality = serializers.FloatField()
    category_breakdown = serializers.DictField()
    top_contributors = serializers.ListField()
    recent_contributions = ContributionLogSerializer(many=True)


class ContributionFlagSerializer(serializers.ModelSerializer):
    flagged_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContributionFlag
        fields = [
            'id', 'contribution', 'flagged_by', 'flagged_by_name',
            'reason', 'resolved', 'resolved_by', 'created_at', 'resolved_at',
        ]

    def get_flagged_by_name(self, obj):
        return obj.flagged_by.full_name or obj.flagged_by.email
