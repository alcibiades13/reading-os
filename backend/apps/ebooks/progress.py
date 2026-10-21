"""
Connects an e-book's reading position to the user's library entry (UserBook):
progress sync, finishing a book and logging reading sessions.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.books.models import Author, Book
from apps.reading.models import BookReadLog, ReadingSession, UserBook

# Sessions shorter than this aren't worth logging (opening a book to check something)
MIN_SESSION_SECONDS = 60


def find_or_create_catalog_book(ebook):
    """Match the file to an existing catalog book (ISBN, then title + author), or create one."""
    if ebook.isbn:
        book = Book.objects.filter(isbn=ebook.isbn).first()
        if book:
            return book

    book = (
        Book.objects
        .filter(title__iexact=ebook.title.strip(), authors__name__iexact=ebook.author.strip())
        .first()
    )
    if book:
        return book

    with transaction.atomic():
        book = Book.objects.create(
            title=ebook.title.strip(),
            isbn=ebook.isbn or None,
            language=(ebook.language or 'sr')[:10],
            pages=ebook.page_count if ebook.format == ebook.FORMAT_PDF else None,
            source='manual',
            last_modified_by=ebook.user,
        )
        for name in [n.strip() for n in ebook.author.split(',') if n.strip()]:
            author, _ = Author.objects.get_or_create(name=name)
            book.authors.add(author)
    return book


def get_user_book(ebook):
    if not ebook.book_id:
        return None
    return (
        UserBook.objects
        .filter(user=ebook.user, book_id=ebook.book_id, replaced_by__isnull=True)
        .select_related('book')
        .first()
    )


def total_pages(ebook):
    """Page count used to turn a progress fraction into a page number."""
    if ebook.book_id and ebook.book.pages:
        return ebook.book.pages
    if ebook.format == ebook.FORMAT_PDF and ebook.page_count:
        return ebook.page_count
    return None


def page_for_progress(ebook, progress):
    pages = total_pages(ebook)
    if not pages or progress is None:
        return None
    return min(pages, max(1, round(progress * pages)))


def enable_tracking(ebook, book=None, pages=None):
    """Link the file to a catalog book and make sure it's on the user's shelf as 'currently reading'."""
    if book is not None:
        ebook.book = book
    elif not ebook.book_id:
        ebook.book = find_or_create_catalog_book(ebook)

    # Fill in a missing page count so progress can be expressed in pages
    if pages and not ebook.book.pages:
        ebook.book.pages = pages
        ebook.book.save(update_fields=['pages'])

    ebook.track_progress = True
    ebook.save(update_fields=['book', 'track_progress', 'updated_at'])

    user_book = get_user_book(ebook)
    today = timezone.now().date()
    if user_book is None:
        user_book = UserBook.objects.create(
            user=ebook.user,
            book=ebook.book,
            status='currently_reading',
            started_at=today,
        )
    elif user_book.status == 'want_to_read':
        user_book.status = 'currently_reading'
        user_book.started_at = user_book.started_at or today
        user_book.save(update_fields=['status', 'started_at', 'updated_at'])

    sync_progress(ebook)
    return user_book


def sync_progress(ebook):
    """
    Copy the e-book position to UserBook.current_page. Only moves forward
    ("furthest page read"), so flipping back to look something up doesn't lose progress.
    Uses a queryset update on purpose: the post_save progress signal would otherwise
    post a feed item on every page turn.
    """
    if not ebook.track_progress or not ebook.book_id:
        return
    page = page_for_progress(ebook, ebook.progress)
    if not page:
        return
    UserBook.objects.filter(
        user=ebook.user,
        book_id=ebook.book_id,
        replaced_by__isnull=True,
        current_page__lt=page,
    ).exclude(status='read').update(current_page=page, updated_at=timezone.now())


def finish(ebook):
    """Mark the linked library entry as read (same side effects as finishing a book in the app)."""
    user_book = get_user_book(ebook)
    if user_book is None or user_book.status == 'read':
        return user_book

    today = timezone.now().date()
    user_book.status = 'read'
    user_book.finished_at = today
    user_book.started_at = user_book.started_at or today
    if user_book.book.pages:
        user_book.current_page = user_book.book.pages
    user_book.save()

    BookReadLog.objects.create(user_book=user_book, started_at=user_book.started_at, finished_at=today)

    from apps.challenges.models import ReadingChallenge
    for challenge in ReadingChallenge.objects.filter(user=ebook.user, is_active=True):
        challenge.update_progress()
    return user_book


def record_session(ebook, duration_seconds, start_progress, end_progress):
    """Log time spent in the reader as a ReadingSession (feeds reading stats)."""
    if duration_seconds < MIN_SESSION_SECONDS or not ebook.track_progress:
        return None
    user_book = get_user_book(ebook)
    if user_book is None:
        return None

    start_page = page_for_progress(ebook, start_progress) or 0
    end_page = page_for_progress(ebook, end_progress) or start_page
    return ReadingSession.objects.create(
        user=ebook.user,
        user_book=user_book,
        duration_seconds=int(duration_seconds),
        start_page=start_page,
        end_page=end_page,
        pages_read=max(0, end_page - start_page),
        started_at=timezone.now() - timedelta(seconds=int(duration_seconds)),
    )
