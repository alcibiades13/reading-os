from django.db import models
from django.conf import settings
from django.utils.text import slugify

from apps.books.models import Book


class ReadingList(models.Model):
    """
    Custom user reading lists.
    Can be regular lists or "smart lists" (auto-populated by filters).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_lists'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    
    # Smart list functionality
    is_smart = models.BooleanField(
        default=False,
        help_text="Auto-populate based on filter rules"
    )
    filter_rules = models.JSONField(
        null=True,
        blank=True,
        help_text="Filter criteria for smart lists"
    )
    
    # Privacy settings
    is_public = models.BooleanField(
        default=False,
        help_text="Make list visible to everyone"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Reading List'
        verbose_name_plural = 'Reading Lists'
        unique_together = ['user', 'slug']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Ensure unique slug per user
            while ReadingList.objects.filter(
                user=self.user,
                slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    @property
    def books_count(self):
        """Number of books in this list"""
        return self.items.count()


class ReadingListItem(models.Model):
    """
    Individual book in a reading list.
    Supports manual ordering and personal notes.
    """
    reading_list = models.ForeignKey(
        ReadingList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='list_items'
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Manual ordering within the list"
    )
    note = models.TextField(
        blank=True,
        help_text="Personal note about why this book is in the list"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['reading_list', 'book']
        ordering = ['order', '-added_at']
        verbose_name = 'Reading List Item'
        verbose_name_plural = 'Reading List Items'
    
    def __str__(self):
        return f"{self.reading_list.title} - {self.book.title}"


