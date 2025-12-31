from django.contrib import admin
from .models import Author, Publisher, Genre, Tag, Book


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'birth_date', 'death_date', 'created_at']
    search_fields = ['name', 'bio']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'created_at']
    search_fields = ['name', 'country']
    list_filter = ['country', 'created_at']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'created_at']
    search_fields = ['name']
    list_filter = ['parent', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'created_at']
    search_fields = ['name']
    list_filter = ['category', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_names', 'publisher', 'isbn', 'language', 'source', 'created_at']
    search_fields = ['title', 'subtitle', 'isbn', 'authors__name']
    list_filter = ['language', 'source', 'genres', 'created_at']
    filter_horizontal = ['authors', 'genres', 'tags']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'isbn', 'description')
        }),
        ('Authors & Publisher', {
            'fields': ('authors', 'publisher')
        }),
        ('Publishing Details', {
            'fields': ('published_date', 'language', 'pages', 'cover_image')
        }),
        ('Categorization', {
            'fields': ('genres', 'tags')
        }),
        ('Source Tracking', {
            'fields': ('source', 'external_ids')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def author_names(self, obj):
        """Display authors in list view"""
        return obj.author_names
    author_names.short_description = 'Authors'

