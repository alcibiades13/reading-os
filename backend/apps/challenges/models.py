from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from apps.books.models import Genre, Tag


class ReadingChallenge(models.Model):
    """
    Challenges/goals (yearly or custom periods).
    Supports books, vocabulary words, quotes, and manuscript words.
    """
    TYPE_BOOKS = 'books'
    TYPE_VOCABULARY = 'vocabulary_words'
    TYPE_QUOTES = 'quotes'
    TYPE_MANUSCRIPT = 'manuscript_words'

    CHALLENGE_TYPES = [
        (TYPE_BOOKS, 'Books Read'),
        (TYPE_VOCABULARY, 'Vocabulary Words'),
        (TYPE_QUOTES, 'Quotes Collected'),
        (TYPE_MANUSCRIPT, 'Manuscript Words'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='challenges'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    challenge_type = models.CharField(
        max_length=20,
        choices=CHALLENGE_TYPES,
        default=TYPE_BOOKS,
    )

    # Goal settings
    target_books = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Target count (books/words/quotes depending on type)"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    # Optional filters (books challenge only)
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
        help_text="Current count (auto-calculated)"
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
        """Recalculate completed count based on challenge type."""
        if self.challenge_type == self.TYPE_BOOKS:
            self._update_books_progress()
        elif self.challenge_type == self.TYPE_VOCABULARY:
            self._update_vocabulary_progress()
        elif self.challenge_type == self.TYPE_QUOTES:
            self._update_quotes_progress()
        elif self.challenge_type == self.TYPE_MANUSCRIPT:
            self._update_manuscript_progress()

    def _update_books_progress(self):
        from apps.reading.models import BookReadLog
        logs = BookReadLog.objects.filter(
            user_book__user=self.user,
            finished_at__gte=self.start_date,
            finished_at__lte=self.end_date,
        )
        if self.genre_filter.exists():
            logs = logs.filter(user_book__book__genres__in=self.genre_filter.all())
        if self.tag_filter.exists():
            logs = logs.filter(user_book__book__tags__in=self.tag_filter.all())
        if self.min_pages:
            logs = logs.filter(user_book__book__pages__gte=self.min_pages)
        self.completed_books = logs.values('user_book__book').distinct().count()
        self.save(update_fields=['completed_books'])

    def _update_vocabulary_progress(self):
        from apps.reading.models import VocabularyWord
        count = VocabularyWord.objects.filter(
            user=self.user,
            created_at__date__gte=self.start_date,
            created_at__date__lte=self.end_date,
        ).count()
        self.completed_books = count
        self.save(update_fields=['completed_books'])

    def _update_quotes_progress(self):
        from apps.reading.models import Quote
        count = Quote.objects.filter(
            user=self.user,
            created_at__date__gte=self.start_date,
            created_at__date__lte=self.end_date,
        ).count()
        self.completed_books = count
        self.save(update_fields=['completed_books'])

    def _update_manuscript_progress(self):
        from apps.codex.models import ManuscriptChapter
        from django.db.models import Sum
        import re
        chapters = ManuscriptChapter.objects.filter(
            manuscript__user=self.user,
            updated_at__date__gte=self.start_date,
            updated_at__date__lte=self.end_date,
        )
        total = 0
        for ch in chapters:
            text = re.sub(r'<[^>]+>', ' ', ch.content or '')
            total += len(text.split())
        self.completed_books = total
        self.save(update_fields=['completed_books'])


# Signal to update challenge progress when a book is finished
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.reading.models import UserBook


@receiver(post_save, sender=UserBook)
def update_challenge_progress_books(sender, instance, **kwargs):
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


from apps.reading.models import VocabularyWord


@receiver(post_save, sender=VocabularyWord)
def update_challenge_progress_vocabulary(sender, instance, **kwargs):
    """Update vocabulary_words challenges when a new word is added."""
    created_date = instance.created_at.date()
    active_challenges = ReadingChallenge.objects.filter(
        user=instance.user,
        challenge_type=ReadingChallenge.TYPE_VOCABULARY,
        is_active=True,
        start_date__lte=created_date,
        end_date__gte=created_date,
    )
    for challenge in active_challenges:
        challenge.update_progress()


class ReadingSchedule(models.Model):
    """A named reading plan containing ordered sections."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_schedules'
    )
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ReadingScheduleSection(models.Model):
    """A section (e.g. month) within a reading schedule, containing ordered book IDs."""
    schedule = models.ForeignKey(
        ReadingSchedule,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    book_ids = models.JSONField(default=list, help_text="Ordered list of book IDs")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.schedule.title} / {self.title}"
