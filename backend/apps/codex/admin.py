from django.contrib import admin
from apps.codex.models import JournalEntry, Manuscript, Chapter


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'mood', 'created_at']
    list_filter = ['mood', 'created_at']
    search_fields = ['title', 'content']


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ['order', 'title', 'word_count']
    readonly_fields = ['word_count']


@admin.register(Manuscript)
class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'genre', 'current_word_count', 'target_word_count', 'updated_at']
    list_filter = ['genre', 'created_at']
    search_fields = ['title', 'subtitle']
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['title', 'manuscript', 'order', 'word_count', 'updated_at']
    list_filter = ['manuscript']
