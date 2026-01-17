from django.contrib import admin
from .models import ReadingList, ReadingListItem


class ReadingListItemInline(admin.TabularInline):
    """Inline display of list items within ReadingList admin"""
    model = ReadingListItem
    extra = 1
    fields = ['book', 'order', 'note']


@admin.register(ReadingList)
class ReadingListAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_smart', 'is_public', 'books_count', 'created_at']
    list_filter = ['is_smart', 'is_public', 'created_at']
    search_fields = ['user__email', 'title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ReadingListItemInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'title', 'slug', 'description')
        }),
        ('Smart List', {
            'fields': ('is_smart', 'filter_rules'),
            'classes': ('collapse',)
        }),
        ('Privacy', {
            'fields': ('is_public',)
        }),
    )


@admin.register(ReadingListItem)
class ReadingListItemAdmin(admin.ModelAdmin):
    list_display = ['reading_list', 'book', 'order', 'added_at']
    list_filter = ['added_at']
    search_fields = ['reading_list__title', 'book__title', 'note']


