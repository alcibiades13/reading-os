from django.contrib import admin

from apps.contributions.models import (
    ContributionLog, UserReputation, Badge, UserBadge, ContributionFlag,
)


@admin.register(ContributionLog)
class ContributionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'category', 'awarded_points', 'quality_status', 'created_at']
    list_filter = ['action', 'category', 'quality_status', 'is_reverted']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'total_points', 'total_contributions', 'quality_ratio']
    list_filter = ['tier']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'icon', 'is_active']
    list_filter = ['category', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'awarded_at', 'awarded_by']
    list_filter = ['badge']
    search_fields = ['user__email', 'badge__name']


@admin.register(ContributionFlag)
class ContributionFlagAdmin(admin.ModelAdmin):
    list_display = ['contribution', 'flagged_by', 'reason', 'resolved', 'created_at']
    list_filter = ['resolved']
