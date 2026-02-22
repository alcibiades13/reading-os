from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify

from apps.books.models import Book

# Import StudyNote model
from .models_study import StudyNote


class UserBook(models.Model):
    """
    Represents user's relationship with a book.
    Central model for tracking reading progress and personal ratings.
    """
    STATUS_CHOICES = [
        ('want_to_read', 'Want to Read'),
        ('currently_reading', 'Currently Reading'),
        ('read', 'Read'),
        ('abandoned', 'Abandoned'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_books'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='user_books'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='want_to_read'
    )
    
    # Reading tracking
    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    current_page = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Personal rating & review
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.5), MaxValueValidator(10.0)],
        help_text="Rating from 0.5 to 10.0 (half-star increments)"
    )
    review = models.TextField(
        blank=True,
        help_text="Personal review/thoughts"
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text="Mark as favorite book"
    )
    
    # Calculated metrics (updated via signals)
    quotes_count = models.IntegerField(
        default=0,
        help_text="Number of quotes extracted from this book"
    )
    depth_score = models.FloatField(
        default=0.0,
        help_text="Engagement score: quotes_count / pages * factors"
    )
    
    # Ownership
    is_owned = models.BooleanField(
        default=False,
        help_text="User physically owns this book"
    )

    # Privacy
    is_public = models.BooleanField(
        default=True,
        help_text="Show this book on public profile"
    )

    # Edition Management
    replaced_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replaces',
        help_text="If user switched to different edition, points to new UserBook"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'book']
        ordering = ['-updated_at']
        verbose_name = 'User Book'
        verbose_name_plural = 'User Books'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['user', 'is_owned']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.book.title} ({self.status})"
    
    def calculate_depth_score(self):
        """
        Calculate engagement depth score.
        Formula: (quotes_count / pages) * 100 if pages > 0
        """
        if self.book.pages and self.book.pages > 0:
            self.depth_score = (self.quotes_count / self.book.pages) * 100
        else:
            self.depth_score = self.quotes_count * 0.5
        self.save(update_fields=['depth_score'])
    
    @property
    def reading_progress(self):
        """Calculate reading progress percentage"""
        if self.book.pages and self.book.pages > 0:
            return min((self.current_page / self.book.pages) * 100, 100)
        return 0

    @property
    def is_active(self):
        """Check if this is the active edition (not replaced)"""
        return self.replaced_by is None


class QuoteTag(models.Model):
    """
    User-defined tags for organizing quotes.
    Examples: "duhovnost", "prijateljstvo", "bol", "stoicizam"
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quote_tags'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text="Hex color code for visual distinction"
    )
    
    # AI suggestions (for later)
    is_ai_suggested = models.BooleanField(
        default=False,
        help_text="Was this tag suggested by AI?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'slug']
        ordering = ['name']
        verbose_name = 'Quote Tag'
        verbose_name_plural = 'Quote Tags'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class Quote(models.Model):
    """
    CENTRAL MODEL - User's extracted quotes from books.
    This is the heart of your application!
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,
        blank=True,
        help_text="Optional: Link to book in database"
    )
    user_book = models.ForeignKey(
        UserBook,
        on_delete=models.CASCADE,
        related_name='quotes',
        null=True,
        blank=True,
        help_text="Optional: Link to user's book entry"
    )

    # Manual book info (when book not in database)
    book_title = models.CharField(
        max_length=500,
        blank=True,
        help_text="Book title (if not linked to database book)"
    )
    book_author = models.CharField(
        max_length=500,
        blank=True,
        help_text="Book author (if not linked to database book)"
    )

    # Quote content
    text = models.TextField(help_text="The actual quote text")
    page_number = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    chapter = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Chapter name or number"
    )
    
    # Personal notes
    note = models.TextField(
        blank=True,
        help_text="Your personal thoughts/reflections on this quote"
    )
    
    # Organization
    tags = models.ManyToManyField(
        QuoteTag,
        related_name='quotes',
        blank=True
    )
    is_favorite = models.BooleanField(
        default=False,
        help_text="Mark as favorite quote"
    )
    
    # Sharing settings
    is_public = models.BooleanField(
        default=False,
        help_text="Share publicly (on profile)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'
        indexes = [
            models.Index(fields=['user', 'book']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        book_info = self.book.title if self.book else (self.book_title or "Unknown Book")
        return f"{book_info} - {text_preview}"


class VocabularyWord(models.Model):
    """Model for storing vocabulary words learned from reading"""
    MASTERY_CHOICES = [
        ('new', 'New'),
        ('learning', 'Learning'),
        ('mastered', 'Mastered'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vocabulary_words'
    )
    word = models.CharField(max_length=200)
    definition = models.TextField()
    context = models.TextField(blank=True, help_text="Example sentence")

    # Optional book reference
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vocabulary_words'
    )
    book_title = models.CharField(max_length=500, blank=True)
    book_author = models.CharField(max_length=500, blank=True)
    page_number = models.IntegerField(null=True, blank=True)

    # Learning progress
    mastery = models.CharField(
        max_length=20,
        choices=MASTERY_CHOICES,
        default='new'
    )
    review_count = models.IntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    # Tags and metadata
    tags = models.JSONField(default=list, blank=True)
    is_favorite = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vocabulary Word'
        verbose_name_plural = 'Vocabulary Words'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'mastery']),
            models.Index(fields=['word']),
        ]

    def __str__(self):
        return f"{self.word} - {self.user.email}"


# Signals to update UserBook.quotes_count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Quote)
def update_quotes_count_on_create(sender, instance, created, **kwargs):
    """Update UserBook quotes_count when Quote is created"""
    if created and instance.user_book:
        user_book = instance.user_book
        user_book.quotes_count = user_book.quotes.count()
        user_book.save(update_fields=['quotes_count'])
        user_book.calculate_depth_score()


@receiver(post_delete, sender=Quote)
def update_quotes_count_on_delete(sender, instance, **kwargs):
    """Update UserBook quotes_count when Quote is deleted"""
    if instance.user_book:
        try:
            user_book = instance.user_book
            user_book.quotes_count = user_book.quotes.count()
            user_book.save(update_fields=['quotes_count'])
            user_book.calculate_depth_score()
        except UserBook.DoesNotExist:
            pass


@receiver(post_save, sender=UserBook)
def create_feed_item_on_progress(sender, instance, created, update_fields, **kwargs):
    """Create feed item when user updates reading progress"""
    # Don't create feed items on initial creation
    if created:
        return

    # Only create feed items if current_page was updated
    if update_fields and 'current_page' in update_fields:
        from apps.social.models import FeedItem

        # Only create if the book has meaningful progress
        if instance.current_page and instance.current_page > 0:
            # Calculate progress percentage
            if instance.book.pages:
                progress_percent = int((instance.current_page / instance.book.pages) * 100)
                preview_text = f"Updated progress on {instance.book.title}: {instance.current_page}/{instance.book.pages} pages ({progress_percent}%)"
            else:
                preview_text = f"Updated progress on {instance.book.title}: {instance.current_page} pages"

            # Create feed item for the user
            FeedItem.objects.create(
                user=instance.user,
                actor=instance.user,
                feed_type='progress_update',
                content_type='UserBook',
                object_id=instance.id,
                preview_text=preview_text,
                preview_image=instance.book.cover_image or ''
            )


