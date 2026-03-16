import uuid
from django.db import models
from django.conf import settings


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def deleted_only(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

    def with_deleted(self):
        return super().get_queryset()


class JournalEntry(models.Model):
    """
    Personal journal/reflection entry for the Codex feature.
    """
    MOOD_CHOICES = [
        ('contemplative', 'Contemplative'),
        ('inspired', 'Inspired'),
        ('melancholic', 'Melancholic'),
        ('energetic', 'Energetic'),
        ('serene', 'Serene'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal_entries'
    )
    title = models.CharField(max_length=500, default='Untitled Reflection')
    content = models.TextField(blank=True)
    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        default='serene'
    )
    tags = models.JSONField(default=list, blank=True)
    is_locked = models.BooleanField(default=False)

    # Optional book reference
    book = models.ForeignKey(
        'books.Book',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='journal_entries',
        db_index=True,
    )

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def word_count(self):
        return len(self.content.split()) if self.content else 0


class Manuscript(models.Model):
    """
    A manuscript/book project that the user is writing.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='manuscripts'
    )
    title = models.CharField(max_length=500, default='Untitled Manuscript')
    subtitle = models.CharField(max_length=500, blank=True)
    genre = models.CharField(max_length=100, default='Fiction')
    cover_color = models.CharField(max_length=20, default='#6366f1')
    target_word_count = models.IntegerField(default=50000)

    # Sharing
    is_shared = models.BooleanField(default=False)
    share_token = models.UUIDField(null=True, blank=True, unique=True)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Manuscript'
        verbose_name_plural = 'Manuscripts'

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def current_word_count(self):
        return sum(ch.word_count for ch in self.chapters.all())

    @property
    def completion_percentage(self):
        if self.target_word_count == 0:
            return 0
        return min(100, round((self.current_word_count / self.target_word_count) * 100))


class Chapter(models.Model):
    """
    A chapter within a manuscript.
    """
    manuscript = models.ForeignKey(
        Manuscript,
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    title = models.CharField(max_length=500, default='Untitled Chapter')
    content = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Chapter'
        verbose_name_plural = 'Chapters'

    def __str__(self):
        return f"Ch. {self.order}: {self.title} ({self.manuscript.title})"

    @property
    def word_count(self):
        return len(self.content.split()) if self.content else 0
