from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class StudyNote(models.Model):
    """
    Study notes for deep reading and scholarship.
    Separate from regular quotes for focused study sessions.
    """

    NOTE_TYPE_CHOICES = [
        ('note', 'Note'),           # Personal thoughts/insights
        ('quote', 'Quote'),         # Direct passage from the book
        ('question', 'Question'),   # Something to explore further
        ('insight', 'Insight'),     # Key takeaway or revelation
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_notes')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='study_notes')
    user_book = models.ForeignKey('UserBook', on_delete=models.CASCADE, related_name='study_notes', null=True, blank=True)

    # Content
    reference = models.CharField(
        max_length=255,
        help_text="e.g., 'John 3:16', 'Chapter 5', 'Page 142', 'Letter 12'"
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='note')
    content = models.TextField(help_text="The note content (supports markdown)")

    # Optional fields
    page_number = models.IntegerField(null=True, blank=True)
    chapter = models.CharField(max_length=100, blank=True)

    # Tags (many-to-many with QuoteTag - reuse existing tag system)
    tags = models.ManyToManyField('QuoteTag', blank=True, related_name='study_notes')

    # Promotion
    is_promoted_to_quote = models.BooleanField(
        default=False,
        help_text="Whether this study note has been promoted to a main quote"
    )
    promoted_quote = models.OneToOneField(
        'Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_study_note'
    )

    # Metadata
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reference', '-created_at']
        indexes = [
            models.Index(fields=['user', 'book']),
            models.Index(fields=['reference']),
            models.Index(fields=['note_type']),
        ]

    def __str__(self):
        return f"{self.reference} - {self.get_note_type_display()}"

    @property
    def references_list(self):
        """Return list of references split by comma"""
        if not self.reference:
            return []
        return [ref.strip() for ref in self.reference.split(',') if ref.strip()]

    @property
    def book_title(self):
        return self.book.title if self.book else None

    @property
    def book_author(self):
        if self.book and self.book.authors.exists():
            return ', '.join([author.name for author in self.book.authors.all()])
        return None
