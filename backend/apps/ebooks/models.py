import uuid
from django.conf import settings
from django.core.files.storage import storages
from django.db import models


def ebook_storage():
    """Private storage for e-book files (local disk in dev, S3/R2 in production)."""
    return storages['ebooks']


def ebook_file_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else instance.format
    return f'ebooks/{instance.user_id}/{uuid.uuid4().hex}.{ext}'


def ebook_cover_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'ebooks/{instance.user_id}/covers/{uuid.uuid4().hex}.{ext}'


class EBook(models.Model):
    """
    An EPUB/PDF file uploaded by a user. Files are private: only the owner
    can download them (served through an authenticated endpoint, never /media).
    """
    FORMAT_EPUB = 'epub'
    FORMAT_PDF = 'pdf'
    FORMAT_CHOICES = [
        (FORMAT_EPUB, 'EPUB'),
        (FORMAT_PDF, 'PDF'),
    ]

    SOURCE_UPLOAD = 'upload'
    SOURCE_GUTENBERG = 'gutenberg'
    SOURCE_CHOICES = [
        (SOURCE_UPLOAD, 'Uploaded by the user'),
        (SOURCE_GUTENBERG, 'Project Gutenberg (public domain)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ebooks'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ebooks',
        help_text="Catalog book this file is an edition of (optional)"
    )

    # Metadata (pre-filled from the file, confirmed by the user)
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=500)
    language = models.CharField(max_length=20, blank=True)
    isbn = models.CharField(max_length=20, blank=True)

    # File
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file = models.FileField(upload_to=ebook_file_path, storage=ebook_storage, max_length=255)
    cover = models.FileField(upload_to=ebook_cover_path, storage=ebook_storage, max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=255, blank=True)
    page_count = models.IntegerField(null=True, blank=True, help_text="PDF page count")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_UPLOAD)
    source_id = models.CharField(max_length=50, blank=True, help_text="ID in the source catalog (e.g. Gutenberg book id)")

    # Reading position
    position = models.CharField(
        max_length=1000,
        blank=True,
        help_text="EPUB CFI or PDF page number"
    )
    progress = models.FloatField(default=0, help_text="0..1")
    track_progress = models.BooleanField(
        null=True,
        blank=True,
        help_text="Sync progress to the user's library entry. Null = not asked yet"
    )
    last_opened_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_opened_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-last_opened_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.format}) - {self.user}"
