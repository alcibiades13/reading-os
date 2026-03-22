from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from apps.books.models import Genre, Tag


class ReadingChallenge(models.Model):
    """
    Reading challenges/goals (yearly or custom periods).
    Examples: "Read 50 books in 2025", "Read 10 spiritual books this year"
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='challenges'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Goal settings
    target_books = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Target number of books to read"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Optional filters (to make challenge more specific)
    genre_filter = models.ManyToManyField(
        Genre,
        blank=True,
        help_text="Only count books from these genres"
    )
    tag_filter = models.ManyToManyField(
        Tag,
        blank=True,
        help_text="Only count books with these tags"
    )
    min_pages = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum pages per book to count"
    )
    
    # Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Is this challenge currently active?"
    )
    completed_books = models.IntegerField(
        default=0,
        help_text="Number of books completed (auto-calculated)"
    )
    
    # Privacy
    is_public = models.BooleanField(
        default=False,
        help_text="Share challenge progress publicly"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Reading Challenge'
        verbose_name_plural = 'Reading Challenges'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Calculate challenge progress as percentage"""
        if self.target_books > 0:
            return min((self.completed_books / self.target_books) * 100, 100)
        return 0
    
    @property
    def is_completed(self):
        """Check if challenge is completed"""
        return self.completed_books >= self.target_books
    
    def update_progress(self):
        """
        Recalculate completed_books based on UserBooks that match criteria.
        Called when a book is finished.
        """
        from apps.reading.models import UserBook
        from django.db.models import Q
        
        # Base query: finished books in date range
        query = Q(
            user=self.user,
            status='read',
            finished_at__gte=self.start_date,
            finished_at__lte=self.end_date
        )
        
        user_books = UserBook.objects.filter(query)
        
        # Apply genre filter if exists
        if self.genre_filter.exists():
            user_books = user_books.filter(
                book__genres__in=self.genre_filter.all()
            )
        
        # Apply tag filter if exists
        if self.tag_filter.exists():
            user_books = user_books.filter(
                book__tags__in=self.tag_filter.all()
            )
        
        # Apply minimum pages filter if exists
        if self.min_pages:
            user_books = user_books.filter(
                book__pages__gte=self.min_pages
            )
        
        self.completed_books = user_books.distinct().count()
        self.save(update_fields=['completed_books'])


# Signal to update challenge progress when a book is finished
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.reading.models import UserBook


@receiver(post_save, sender=UserBook)
def update_challenge_progress(sender, instance, **kwargs):
    """
    Update all active challenges when a UserBook status changes to 'read'.
    Also logs challenge_completed contribution when a challenge is newly completed.
    """
    if instance.status == 'read' and instance.finished_at:
        from apps.contributions.models import ContributionLog
        from apps.contributions.signals import create_contribution

        active_challenges = ReadingChallenge.objects.filter(
            user=instance.user,
            is_active=True,
            start_date__lte=instance.finished_at,
            end_date__gte=instance.finished_at
        )

        for challenge in active_challenges:
            was_completed = challenge.is_completed
            challenge.update_progress()
            # Log contribution if challenge just became completed
            if not was_completed and challenge.is_completed:
                already_logged = ContributionLog.objects.filter(
                    user=instance.user,
                    action='challenge_completed',
                    content_type='ReadingChallenge',
                    object_id=challenge.id,
                ).exists()
                if not already_logged:
                    create_contribution(
                        instance.user, 'challenge_completed',
                        'ReadingChallenge', challenge.id,
                        metadata={'title': challenge.title},
                    )


