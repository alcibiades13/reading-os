from django.contrib import admin
from .models import ReadingChallenge


@admin.register(ReadingChallenge)
class ReadingChallengeAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'target_books', 'completed_books', 'progress_percentage', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'is_public', 'start_date', 'created_at']
    search_fields = ['user__email', 'title', 'description']
    filter_horizontal = ['genre_filter', 'tag_filter']
    readonly_fields = ['completed_books', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User & Title', {
            'fields': ('user', 'title', 'description')
        }),
        ('Goal Settings', {
            'fields': ('target_books', 'start_date', 'end_date')
        }),
        ('Filters (Optional)', {
            'fields': ('genre_filter', 'tag_filter', 'min_pages'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('is_active', 'completed_books')
        }),
        ('Privacy', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_percentage(self, obj):
        """Show progress as percentage"""
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = 'Progress'
    
    actions = ['recalculate_progress']
    
    def recalculate_progress(self, request, queryset):
        """Admin action to recalculate progress for selected challenges"""
        for challenge in queryset:
            challenge.update_progress()
        self.message_user(request, f"Progress recalculated for {queryset.count()} challenges.")
    recalculate_progress.short_description = "Recalculate progress"


