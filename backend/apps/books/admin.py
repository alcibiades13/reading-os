from django.contrib import admin
from .models import (
    Author, Publisher, Genre, Tag, Book, BookDNA, BookDNAVote,
    BookGroup, BookGroupDNA
)


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


@admin.register(BookGroup)
class BookGroupAdmin(admin.ModelAdmin):
    list_display = ['canonical_title', 'get_authors', 'editions_count', 'created_at']
    search_fields = ['canonical_title']
    list_filter = ['created_at']
    filter_horizontal = ['canonical_authors']
    readonly_fields = ['created_at', 'updated_at', 'editions_count']

    fieldsets = (
        ('Basic Information', {
            'fields': ('canonical_title', 'canonical_authors', 'description')
        }),
        ('Stats', {
            'fields': ('editions_count',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_authors(self, obj):
        """Display authors in list view"""
        try:
            authors = ", ".join([a.name for a in obj.canonical_authors.all()[:3]])
            if obj.canonical_authors.count() > 3:
                authors += "..."
            return authors
        except:
            return "-"
    get_authors.short_description = 'Authors'


@admin.register(BookGroupDNA)
class BookGroupDNAAdmin(admin.ModelAdmin):
    list_display = ['book_group', 'pace', 'complexity', 'emotional_intensity', 'darkness', 'source', 'vote_count', 'confidence_score']
    search_fields = ['book_group__canonical_title']
    list_filter = ['source', 'confidence_score']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Book Group', {
            'fields': ('book_group',)
        }),
        ('DNA Attributes', {
            'fields': ('pace', 'complexity', 'emotional_intensity', 'darkness', 'character_focus', 'introspection')
        }),
        ('Themes', {
            'fields': ('themes',)
        }),
        ('Meta', {
            'fields': ('source', 'vote_count', 'confidence_score', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author_names', 'publisher', 'isbn', 'language', 'book_group', 'is_primary_edition', 'source', 'created_at']
    search_fields = ['title', 'subtitle', 'isbn', 'authors__name']
    list_filter = ['language', 'source', 'book_group', 'is_primary_edition', 'genres', 'created_at']
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
        ('Edition Management', {
            'fields': ('book_group', 'is_primary_edition'),
            'description': 'Link different editions of the same work'
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


@admin.register(BookDNA)
class BookDNAAdmin(admin.ModelAdmin):
    list_display = ['book', 'pace', 'complexity', 'emotional_intensity', 'darkness', 'source', 'vote_count', 'confidence_score']
    search_fields = ['book__title']
    list_filter = ['source', 'confidence_score']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Book', {
            'fields': ('book',)
        }),
        ('DNA Attributes', {
            'fields': ('pace', 'complexity', 'emotional_intensity', 'darkness', 'character_focus', 'introspection')
        }),
        ('Themes', {
            'fields': ('themes',)
        }),
        ('Meta', {
            'fields': ('source', 'vote_count', 'confidence_score', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookDNAVote)
class BookDNAVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'created_at']
    search_fields = ['user__email', 'book__title']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
