import re
from collections import defaultdict
from datetime import timedelta
from difflib import SequenceMatcher

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_api.models import DismissedAuthorPair, DismissedBookPair
from apps.admin_api.permissions import IsAdminUser
from apps.books.models import Author, Book, AuthorGroup, BookGroup, Genre
from apps.contributions.permissions import IsCuratorOrAdmin
from apps.contributions.signals import create_contribution
from apps.reading.models import Quote, VocabularyWord
from apps.users.models import User


def _safe_int(value, default=1, min_val=1):
    """Safely parse an int from query params."""
    try:
        result = int(value)
        return max(min_val, result)
    except (TypeError, ValueError):
        return default


class AdminStatsView(APIView):
    """System-wide statistics for admin dashboard."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        total_books = Book.objects.count()
        total_authors = Author.objects.count()
        total_author_groups = AuthorGroup.objects.count()
        total_users = User.objects.count()
        total_quotes = Quote.objects.count()
        total_vocabulary = VocabularyWord.objects.count()
        total_genres = Genre.objects.count()

        books_this_week = Book.objects.filter(created_at__gte=week_ago).count()
        quotes_this_week = Quote.objects.filter(created_at__gte=week_ago).count()

        books_without_cover = Book.objects.filter(
            Q(cover_image='') | Q(cover_image__isnull=True)
        ).count()
        books_without_isbn = Book.objects.filter(
            Q(isbn='') | Q(isbn__isnull=True)
        ).count()
        books_without_authors = Book.objects.annotate(
            author_count=Count('authors')
        ).filter(author_count=0).count()

        # Health = percentage of books that have cover + isbn + authors
        issues_total = books_without_cover + books_without_isbn + books_without_authors
        max_issues = total_books * 3 if total_books else 1
        health_pct = round(((max_issues - issues_total) / max_issues) * 100, 1) if max_issues else 100

        # Authors with groups vs total
        grouped_authors = Author.objects.exclude(author_group__isnull=True).count()
        author_consistency = round((grouped_authors / total_authors * 100), 1) if total_authors else 100

        recent_books = Book.objects.order_by('-created_at')[:8].values(
            'id', 'title', 'cover_image', 'source', 'created_at'
        )

        return Response({
            'counts': {
                'total_books': total_books,
                'total_authors': total_authors,
                'total_author_groups': total_author_groups,
                'total_users': total_users,
                'total_quotes': total_quotes,
                'total_vocabulary': total_vocabulary,
                'total_genres': total_genres,
            },
            'activity': {
                'books_added_this_week': books_this_week,
                'quotes_this_week': quotes_this_week,
            },
            'data_quality': {
                'books_without_cover': books_without_cover,
                'books_without_isbn': books_without_isbn,
                'books_without_authors': books_without_authors,
                'health_percentage': health_pct,
                'author_consistency': author_consistency,
            },
            'recent_books': list(recent_books),
        })


class AdminDataIssuesPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminDataIssuesView(APIView):
    """Books with data quality issues."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        issue_type = request.query_params.get('type', 'all')
        page = _safe_int(request.query_params.get('page', 1))
        page_size = min(_safe_int(request.query_params.get('page_size', 20), default=20), 100)

        # Compute summaries
        missing_cover = Book.objects.filter(
            Q(cover_image='') | Q(cover_image__isnull=True)
        ).count()
        missing_isbn = Book.objects.filter(
            Q(isbn='') | Q(isbn__isnull=True)
        ).count()
        missing_authors_qs = Book.objects.annotate(
            author_count=Count('authors')
        ).filter(author_count=0)
        missing_authors = missing_authors_qs.count()

        # Duplicate ISBNs
        dup_isbns = (
            Book.objects.exclude(Q(isbn='') | Q(isbn__isnull=True))
            .values('isbn')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        duplicates = dup_isbns.count()

        summary = {
            'missing_cover': missing_cover,
            'missing_isbn': missing_isbn,
            'missing_authors': missing_authors,
            'duplicates': duplicates,
        }

        # Build issues list
        issues = []

        if issue_type in ('all', 'missing_cover'):
            for b in Book.objects.filter(
                Q(cover_image='') | Q(cover_image__isnull=True)
            ).values('id', 'title', 'isbn', 'cover_image', 'created_at')[:200]:
                issues.append({
                    'id': f"cover-{b['id']}",
                    'book_id': b['id'],
                    'title': b['title'],
                    'isbn': b['isbn'],
                    'cover_image': b['cover_image'] or '',
                    'issue_type': 'missing_cover',
                    'description': 'Book has no cover image',
                    'severity': 'medium',
                    'created_at': b['created_at'],
                })

        if issue_type in ('all', 'missing_isbn'):
            for b in Book.objects.filter(
                Q(isbn='') | Q(isbn__isnull=True)
            ).values('id', 'title', 'isbn', 'cover_image', 'created_at')[:200]:
                issues.append({
                    'id': f"isbn-{b['id']}",
                    'book_id': b['id'],
                    'title': b['title'],
                    'isbn': b['isbn'],
                    'cover_image': b['cover_image'] or '',
                    'issue_type': 'missing_isbn',
                    'description': 'Book has no ISBN',
                    'severity': 'low',
                    'created_at': b['created_at'],
                })

        if issue_type in ('all', 'missing_authors'):
            for b in missing_authors_qs.values('id', 'title', 'isbn', 'cover_image', 'created_at')[:200]:
                issues.append({
                    'id': f"authors-{b['id']}",
                    'book_id': b['id'],
                    'title': b['title'],
                    'isbn': b['isbn'],
                    'cover_image': b['cover_image'] or '',
                    'issue_type': 'missing_authors',
                    'description': 'Book has no authors linked',
                    'severity': 'high',
                    'created_at': b['created_at'],
                })

        if issue_type in ('all', 'duplicates'):
            for dup in dup_isbns[:50]:
                books = list(
                    Book.objects.filter(isbn=dup['isbn'])
                    .values('id', 'title', 'cover_image')
                )
                issues.append({
                    'id': f"dup-{dup['isbn']}",
                    'book_id': books[0]['id'] if books else None,
                    'title': f"{dup['count']} books share ISBN {dup['isbn']}",
                    'isbn': dup['isbn'],
                    'cover_image': books[0].get('cover_image', '') if books else '',
                    'issue_type': 'duplicate_isbn',
                    'description': f"{dup['count']} books share the same ISBN",
                    'severity': 'high',
                    'books': books,
                })

        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        issues.sort(key=lambda x: severity_order.get(x['severity'], 3))

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            'count': len(issues),
            'summary': summary,
            'page': page,
            'page_size': page_size,
            'results': issues[start:end],
        })


def _normalize_name(name):
    """Normalize author name: remove dots, collapse spaces, lowercase."""
    name = name.lower().strip()
    name = name.replace('.', '')
    name = re.sub(r'\s+', ' ', name)
    return name


def _auto_link_identical_authors(authors):
    """
    Auto-link authors whose names are identical after normalization
    (e.g. "J.K. Rowling" / "J. K. Rowling", "H. Rider Haggard" / "H Rider Haggard").
    Returns count of auto-linked authors and set of IDs that were linked as variants.
    """
    name_groups = defaultdict(list)
    for author in authors:
        norm = _normalize_name(author.name)
        name_groups[norm].append(author)

    auto_linked = 0
    linked_variant_ids = set()

    for norm_name, group_authors in name_groups.items():
        if len(group_authors) < 2:
            continue

        # Primary = most books
        group_authors.sort(key=lambda a: a.book_count, reverse=True)
        primary = group_authors[0]

        if not primary.author_group:
            group = AuthorGroup.objects.create(canonical_name=primary.name)
            primary.author_group = group
            primary.is_primary_alias = True
            primary.save()

        for other in group_authors[1:]:
            other.author_group = primary.author_group
            other.save()
            auto_linked += 1
            linked_variant_ids.add(other.id)

    return auto_linked, linked_variant_ids


def _first_names_compatible(parts1, parts2):
    """
    Check if the first-name portions of two names are compatible.
    Handles: abbreviations (J. vs John), transliterations (Čarls vs Charles),
    and cross-script initials (J.R.R. vs Dž. R. R.).
    Rejects completely different first names (Borisav vs Ivan, Edgar vs Lew).
    """
    first1 = parts1[:-1]  # everything except last name
    first2 = parts2[:-1]

    # If either has no first name, can't compare — allow match
    if not first1 or not first2:
        return True

    f1_raw = first1[0]
    f2_raw = first2[0]
    f1 = f1_raw.rstrip('.')
    f2 = f2_raw.rstrip('.')

    # Both are abbreviated initials (contain dots) — likely same person
    # in different scripts (e.g. "J.R.R." vs "Dž. R. R.")
    if '.' in f1_raw and '.' in f2_raw:
        return True

    # One is an abbreviation (single letter) — check if initials match
    if len(f1) == 1 or len(f2) == 1:
        return f1[0] == f2[0]

    # Both full names — require similarity for transliterations (Čarls/Charles)
    # but reject completely different names (Borisav/Ivan, Edgar/Lew)
    sim = SequenceMatcher(None, f1, f2).ratio()
    return sim >= 0.5


def _are_potential_duplicates(name1, name2, min_similarity=0.75):
    """
    Check if two author names are potential duplicates.
    Requires: last names similar + first names compatible (abbreviation/transliteration).
    Rejects: same last name but completely different first name (different people).
    """
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()

    parts1 = n1.split()
    parts2 = n2.split()

    if not parts1 or not parts2:
        return False, 0.0

    # Last name = last token in the name
    last1 = parts1[-1]
    last2 = parts2[-1]

    # Last name must be similar — this is the primary gate
    last_sim = SequenceMatcher(None, last1, last2).ratio()
    if last_sim < min_similarity:
        return False, 0.0

    # First names must be compatible (not completely different people)
    if not _first_names_compatible(parts1, parts2):
        return False, 0.0

    # Overall full-name similarity must also pass threshold
    overall = SequenceMatcher(None, n1, n2).ratio()
    if overall < min_similarity:
        return False, 0.0

    return True, overall


class AdminAuthorMergeCandidatesView(APIView):
    """Find all potential author merges across the system."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            min_similarity = float(request.query_params.get('min_similarity', 0.75))
        except (TypeError, ValueError):
            min_similarity = 0.75
        page = _safe_int(request.query_params.get('page', 1))
        page_size = min(_safe_int(request.query_params.get('page_size', 20), default=20), 100)

        # Only ungrouped authors with at least 1 book
        authors = list(
            Author.objects.filter(author_group__isnull=True)
            .annotate(book_count=Count('books'))
            .filter(book_count__gte=1)
            .order_by('-book_count')
        )

        # Auto-link authors with identical normalized names (e.g. "J.K." vs "J. K.")
        auto_linked, linked_ids = _auto_link_identical_authors(authors)
        # Remove auto-linked variants from candidates pool
        if linked_ids:
            authors = [a for a in authors if a.id not in linked_ids]

        # Load dismissed pairs for filtering
        dismissed = DismissedAuthorPair.get_dismissed_set()

        # Bucket authors by last name to avoid O(n²) full comparison.
        # Only compare authors within the same last-name bucket.
        last_name_buckets = defaultdict(list)
        for author in authors:
            parts = author.name.lower().strip().split()
            last = parts[-1] if parts else ''
            last_name_buckets[last].append(author)

        seen_pairs = set()
        candidates = []

        for bucket_authors in last_name_buckets.values():
            if len(bucket_authors) < 2:
                continue
            for i, author in enumerate(bucket_authors):
                variants = []
                for other in bucket_authors[i + 1:]:
                    pair_key = tuple(sorted([author.id, other.id]))
                    if pair_key in seen_pairs:
                        continue
                    if frozenset([author.id, other.id]) in dismissed:
                        continue

                    is_match, similarity = _are_potential_duplicates(
                        author.name, other.name, min_similarity
                    )
                    if is_match:
                        seen_pairs.add(pair_key)
                        variants.append({
                            'id': other.id,
                            'name': other.name,
                            'book_count': other.book_count,
                            'similarity': round(similarity, 3),
                        })

                if variants:
                    variants.sort(key=lambda x: x['similarity'], reverse=True)
                    candidates.append({
                        'primary': {
                            'id': author.id,
                            'name': author.name,
                            'book_count': author.book_count,
                            'photo': author.photo or '',
                        },
                        'variants': variants,
                        'total_books': author.book_count + sum(v['book_count'] for v in variants),
                    })

        # Sort by total_books desc
        candidates.sort(key=lambda x: x['total_books'], reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        # Also fetch existing linked author groups for the unlink UI
        linked_groups = []
        for group in AuthorGroup.objects.prefetch_related('members').order_by('-created_at')[:50]:
            members = list(group.members.all())
            if len(members) < 2:
                continue
            primary = next((m for m in members if m.is_primary_alias), members[0])
            linked_groups.append({
                'group_id': group.id,
                'canonical_name': group.canonical_name,
                'primary': {
                    'id': primary.id,
                    'name': primary.name,
                    'photo': primary.photo or '',
                },
                'members': [
                    {'id': m.id, 'name': m.name, 'is_primary': m.is_primary_alias}
                    for m in members
                ],
            })

        return Response({
            'count': len(candidates),
            'auto_linked': auto_linked,
            'page': page,
            'page_size': page_size,
            'results': candidates[start:end],
            'linked_groups': linked_groups,
        })


class AdminBooksView(APIView):
    """Admin book list with extended info."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.query_params.get('search', '')
        page = _safe_int(request.query_params.get('page', 1))
        page_size = min(_safe_int(request.query_params.get('page_size', 30), default=30), 100)
        filter_type = request.query_params.get('filter', 'all')

        qs = Book.objects.annotate(
            readers_count=Count('user_books', distinct=True),
            quotes_count=Count('quotes', distinct=True),
        ).select_related('publisher').prefetch_related('authors', 'genres')

        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(isbn__icontains=search) |
                Q(authors__name__icontains=search)
            ).distinct()

        if filter_type == 'missing_data':
            qs = qs.filter(
                Q(cover_image='') | Q(cover_image__isnull=True) |
                Q(isbn='') | Q(isbn__isnull=True)
            )
        elif filter_type == 'recent':
            week_ago = timezone.now() - timedelta(days=7)
            qs = qs.filter(created_at__gte=week_ago)

        total = qs.count()
        qs = qs.order_by('-created_at')

        start = (page - 1) * page_size
        end = start + page_size
        books = qs[start:end]

        results = []
        for book in books:
            results.append({
                'id': book.id,
                'title': book.title,
                'isbn': book.isbn or '',
                'cover_image': book.cover_image or '',
                'language': book.language or '',
                'pages': book.pages,
                'source': book.source or '',
                'publisher': book.publisher.name if book.publisher else '',
                'authors': [{'id': a.id, 'name': a.name} for a in book.authors.all()],
                'genres': [{'id': g.id, 'name': g.name} for g in book.genres.all()],
                'readers_count': book.readers_count,
                'quotes_count': book.quotes_count,
                'book_group_id': book.book_group_id,
                'created_at': book.created_at,
            })

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': results,
        })


class AdminDismissAuthorPairView(APIView):
    """Dismiss an author pair so it no longer appears as a merge candidate."""
    permission_classes = [IsCuratorOrAdmin]

    def post(self, request):
        author1_id = request.data.get('author1_id')
        author2_id = request.data.get('author2_id')

        if not author1_id or not author2_id:
            return Response({'error': 'author1_id and author2_id required'}, status=400)

        author1_id = int(author1_id)
        author2_id = int(author2_id)

        DismissedAuthorPair.objects.get_or_create(
            author1_id=min(author1_id, author2_id),
            author2_id=max(author1_id, author2_id),
        )

        # Log contribution
        create_contribution(
            request.user, 'author_pair_dismissed', 'Author', author1_id,
            metadata={'author2_id': author2_id}
        )

        return Response({'success': True})


class AdminUnlinkAuthorView(APIView):
    """Remove an author from its author group (undo a link)."""
    permission_classes = [IsCuratorOrAdmin]

    def post(self, request, author_id):
        try:
            author = Author.objects.get(id=author_id)
        except Author.DoesNotExist:
            return Response({'error': 'Author not found'}, status=404)

        group = author.author_group
        if not group:
            return Response({'error': 'Author is not in any group'}, status=400)

        # Capture previous state for revert
        previous_state = {
            'author_group_id': group.id,
            'is_primary_alias': author.is_primary_alias,
        }

        author.author_group = None
        author.is_primary_alias = False
        author.save()

        # If only one member left in group, ungroup them too and delete the group
        remaining = group.members.all()
        if remaining.count() == 1:
            last = remaining.first()
            last.author_group = None
            last.is_primary_alias = False
            last.save()
            group.delete()
        elif remaining.count() == 0:
            group.delete()

        # Log contribution
        create_contribution(
            request.user, 'author_unlinked', 'Author', author_id,
            previous_state=previous_state,
        )

        return Response({
            'success': True,
            'author_id': author.id,
            'author_name': author.name,
        })


# ─────────────── Book Deduplication ───────────────


def _normalize_title(title):
    """Normalize book title for comparison."""
    title = title.lower().strip()
    # Remove common articles and subtitles
    for prefix in ['the ', 'a ', 'an ']:
        if title.startswith(prefix):
            title = title[len(prefix):]
    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def _books_are_potential_duplicates(book1_data, book2_data, min_similarity=0.75):
    """
    Check if two books are potential duplicates.
    Considers: title similarity, shared authors, matching ISBN.
    """
    # ISBN match is a strong signal
    if (book1_data.get('isbn') and book2_data.get('isbn')
            and book1_data['isbn'] == book2_data['isbn']):
        return True, 1.0

    # Title similarity
    norm1 = _normalize_title(book1_data['title'])
    norm2 = _normalize_title(book2_data['title'])

    if not norm1 or not norm2:
        return False, 0.0

    title_sim = SequenceMatcher(None, norm1, norm2).ratio()

    # Check author overlap
    authors1 = set(book1_data.get('author_ids', []))
    authors2 = set(book2_data.get('author_ids', []))

    # Also check author groups (linked authors)
    groups1 = set(book1_data.get('author_group_ids', []))
    groups2 = set(book2_data.get('author_group_ids', []))

    has_shared_author = bool(authors1 & authors2)
    has_shared_group = bool(groups1 & groups2 - {None})

    if title_sim >= 0.90 and (has_shared_author or has_shared_group):
        return True, title_sim
    if title_sim >= 0.95:
        # Very high title similarity even without shared author
        return True, title_sim

    return False, title_sim


class AdminBookMergeCandidatesView(APIView):
    """Find potential duplicate books across the system."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            min_similarity = float(request.query_params.get('min_similarity', 0.75))
        except (TypeError, ValueError):
            min_similarity = 0.75
        page = _safe_int(request.query_params.get('page', 1))
        page_size = min(_safe_int(request.query_params.get('page_size', 20), default=20), 100)

        # Only ungrouped books
        books = list(
            Book.objects.filter(book_group__isnull=True)
            .prefetch_related('authors', 'authors__author_group')
            .order_by('-created_at')[:500]
        )

        # Pre-compute data for comparison
        books_data = []
        for book in books:
            authors = list(book.authors.all())
            books_data.append({
                'id': book.id,
                'title': book.title,
                'isbn': book.isbn,
                'cover_image': book.cover_image,
                'source': book.source,
                'author_ids': [a.id for a in authors],
                'author_group_ids': [a.author_group_id for a in authors],
                'author_names': ', '.join(a.name for a in authors[:2]),
                'created_at': book.created_at,
            })

        dismissed = DismissedBookPair.get_dismissed_set()
        seen_pairs = set()
        candidates = []

        for i, b1 in enumerate(books_data):
            variants = []
            for j, b2 in enumerate(books_data):
                if i >= j:
                    continue
                pair_key = tuple(sorted([b1['id'], b2['id']]))
                if pair_key in seen_pairs:
                    continue
                if frozenset([b1['id'], b2['id']]) in dismissed:
                    continue

                is_match, similarity = _books_are_potential_duplicates(
                    b1, b2, min_similarity
                )
                if is_match:
                    seen_pairs.add(pair_key)
                    variants.append({
                        'id': b2['id'],
                        'title': b2['title'],
                        'isbn': b2['isbn'],
                        'cover_image': b2['cover_image'],
                        'source': b2['source'],
                        'author_names': b2['author_names'],
                        'similarity': round(similarity, 3),
                    })

            if variants:
                variants.sort(key=lambda x: x['similarity'], reverse=True)
                candidates.append({
                    'primary': {
                        'id': b1['id'],
                        'title': b1['title'],
                        'isbn': b1['isbn'],
                        'cover_image': b1['cover_image'],
                        'source': b1['source'],
                        'author_names': b1['author_names'],
                    },
                    'variants': variants,
                })

        # Fetch existing linked book groups
        linked_groups = []
        for group in BookGroup.objects.prefetch_related(
            'editions', 'editions__authors'
        ).order_by('-created_at')[:50]:
            editions = list(group.editions.all())
            if len(editions) < 2:
                continue
            linked_groups.append({
                'id': group.id,
                'canonical_title': group.canonical_title,
                'editions': [{
                    'id': ed.id,
                    'title': ed.title,
                    'isbn': ed.isbn,
                    'source': ed.source,
                    'cover_image': ed.cover_image,
                    'author_names': ', '.join(a.name for a in ed.authors.all()[:2]),
                    'is_primary': ed.is_primary_edition,
                } for ed in editions],
            })

        total = len(candidates)
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            'count': total,
            'results': candidates[start:end],
            'linked_groups': linked_groups,
        })


class AdminDismissBookPairView(APIView):
    """Dismiss a book pair so it no longer appears as a merge candidate."""
    permission_classes = [IsCuratorOrAdmin]

    def post(self, request):
        book1_id = request.data.get('book1_id')
        book2_id = request.data.get('book2_id')

        if not book1_id or not book2_id:
            return Response({'error': 'book1_id and book2_id required'}, status=400)

        book1_id = int(book1_id)
        book2_id = int(book2_id)

        DismissedBookPair.objects.get_or_create(
            book1_id=min(book1_id, book2_id),
            book2_id=max(book1_id, book2_id),
        )

        create_contribution(
            request.user, 'book_pair_dismissed', 'Book', book1_id,
            metadata={'book2_id': book2_id}
        )

        return Response({'success': True})


class AdminUnlinkBookView(APIView):
    """Remove a book from its book group (undo a link)."""
    permission_classes = [IsCuratorOrAdmin]

    def post(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=404)

        group = book.book_group
        if not group:
            return Response({'error': 'Book is not in any group'}, status=400)

        previous_state = {
            'book_group_id': group.id,
            'is_primary_edition': book.is_primary_edition,
        }

        book.book_group = None
        book.is_primary_edition = False
        book.save()

        remaining = group.editions.all()
        if remaining.count() == 1:
            last = remaining.first()
            last.book_group = None
            last.is_primary_edition = False
            last.save()
            group.delete()
        elif remaining.count() == 0:
            group.delete()
        else:
            group.update_stats()

        return Response({
            'success': True,
            'book_id': book.id,
            'book_title': book.title,
        })


class AdminDeleteBookView(APIView):
    """Delete a book (e.g. a duplicate). Transfers user data to target book if provided."""
    permission_classes = [IsAdminUser]

    def delete(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=404)

        transfer_to_id = request.query_params.get('transfer_to')
        title = book.title
        book_id_deleted = book.id

        with transaction.atomic():
            if transfer_to_id:
                try:
                    target = Book.objects.get(id=int(transfer_to_id))
                except Book.DoesNotExist:
                    return Response({'error': 'Transfer target book not found'}, status=404)

                # Transfer UserBooks
                from apps.reading.models import UserBook
                for ub in UserBook.objects.filter(book=book):
                    if not UserBook.objects.filter(user=ub.user, book=target).exists():
                        ub.book = target
                        ub.save()
                    else:
                        ub.delete()

                # Transfer Quotes
                from apps.reading.models import Quote
                Quote.objects.filter(book=book).update(book=target)

                # Transfer VocabularyWords
                from apps.reading.models import VocabularyWord
                VocabularyWord.objects.filter(book=book).update(book=target)

                # Transfer StudyNotes
                from apps.reading.models import StudyNote
                StudyNote.objects.filter(book=book).update(book=target)

            book.delete()

        return Response({
            'success': True,
            'deleted_book_id': book_id_deleted,
            'deleted_title': title,
            'transferred_to': int(transfer_to_id) if transfer_to_id else None,
        })
