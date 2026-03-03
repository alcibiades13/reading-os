from django.contrib import admin

from apps.admin_api.models import DismissedAuthorPair, DismissedBookPair


@admin.register(DismissedAuthorPair)
class DismissedAuthorPairAdmin(admin.ModelAdmin):
    list_display = ('author1_id', 'author2_id', 'dismissed_at')
    list_filter = ('dismissed_at',)
    ordering = ('-dismissed_at',)


@admin.register(DismissedBookPair)
class DismissedBookPairAdmin(admin.ModelAdmin):
    list_display = ('book1_id', 'book2_id', 'dismissed_at')
    list_filter = ('dismissed_at',)
    ordering = ('-dismissed_at',)
