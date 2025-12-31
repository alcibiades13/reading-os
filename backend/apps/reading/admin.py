from django.contrib import admin
from .models import UserBook, Quote, QuoteTag


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'status', 'rating', 'is_favorite', 'quotes_count', 'depth_score', 'created_at']
    list_filter = ['status', 'is_favorite', 'rating', 'created_at']
    search_fields = ['user__email', 'book__title', 'review']
    readonly_fields = ['quotes_count', 'depth_score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User & Book', {
            'fields': ('user', 'book', 'status')
        }),
        ('Reading Progress', {
            'fields': ('started_at', 'finished_at', 'current_page')
        }),
        ('Personal Rating', {
            'fields': ('rating', 'review', 'is_favorite')
        }),
        ('Metrics (Auto-calculated)', {
            'fields': ('quotes_count', 'depth_score'),
            'classes': ('collapse',)
        }),
        ('Privacy', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuoteTag)
class QuoteTagAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'slug', 'color', 'is_ai_suggested', 'created_at']
    list_filter = ['is_ai_suggested', 'created_at']
    search_fields = ['user__email', 'name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'text_preview', 'page_number', 'is_favorite', 'is_public', 'created_at']
    list_filter = ['is_favorite', 'is_public', 'created_at']
    search_fields = ['user__email', 'book__title', 'text', 'note']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Book', {
            'fields': ('user', 'book', 'user_book')
        }),
        ('Quote Content', {
            'fields': ('text', 'page_number', 'chapter')
        }),
        ('Personal Notes', {
            'fields': ('note',)
        }),
        ('Organization', {
            'fields': ('tags', 'is_favorite')
        }),
        ('Sharing', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show first 50 chars of quote in list view"""
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Quote Text'

