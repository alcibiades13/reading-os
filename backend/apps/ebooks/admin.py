from django.contrib import admin
from apps.ebooks.models import EBook


@admin.register(EBook)
class EBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'format', 'user', 'file_size', 'progress', 'created_at']
    list_filter = ['format']
    search_fields = ['title', 'author', 'user__email']
    raw_id_fields = ['user', 'book']
