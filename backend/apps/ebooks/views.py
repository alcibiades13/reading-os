import mimetypes
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from apps.books.models import Book
from apps.ebooks import progress as ebook_progress
from apps.ebooks import public_domain
from apps.ebooks.serializers import detect_format

from apps.ebooks.models import EBook
from apps.ebooks.serializers import EBookSerializer, EBookUploadSerializer

CONTENT_TYPES = {
    EBook.FORMAT_EPUB: 'application/epub+zip',
    EBook.FORMAT_PDF: 'application/pdf',
}


class EBookPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class EBookViewSet(viewsets.ModelViewSet):
    """
    The current user's private e-books. Files are only ever streamed to the owner
    through the `file` / `cover` actions - they are not reachable via MEDIA_URL.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EBookPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author']
    ordering_fields = ['last_opened_at', 'created_at', 'title']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = EBook.objects.filter(user=self.request.user)
        book = self.request.query_params.get('book')
        if book:
            queryset = queryset.filter(book_id=book)
        return (
            queryset
            .select_related('book')
            .prefetch_related('book__authors')
            # Most recent activity first: last opened, or upload time if never opened
            .annotate(activity=Coalesce('last_opened_at', 'created_at'))
            .order_by('-activity')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return EBookUploadSerializer
        return EBookSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        extra = {}
        if 'position' in serializer.validated_data:
            extra['last_opened_at'] = timezone.now()
        ebook = serializer.save(**extra)
        if 'progress' in serializer.validated_data:
            ebook_progress.sync_progress(ebook)

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        if instance.cover:
            instance.cover.delete(save=False)
        instance.delete()

    def _stream(self, field_file, content_type, filename=None):
        if not field_file:
            raise Http404
        try:
            handle = field_file.open('rb')
        except FileNotFoundError:
            raise Http404
        response = FileResponse(handle, content_type=content_type)
        response['Cache-Control'] = 'private, max-age=86400'
        if filename:
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=['get'])
    def file(self, request, pk=None):
        ebook = self.get_object()
        EBook.objects.filter(pk=ebook.pk).update(last_opened_at=timezone.now())
        ascii_name = ebook.original_filename.encode('ascii', 'ignore').decode() or f'book.{ebook.format}'
        return self._stream(ebook.file, CONTENT_TYPES[ebook.format], ascii_name.replace('"', ''))

    @action(detail=True, methods=['get'])
    def cover(self, request, pk=None):
        ebook = self.get_object()
        content_type = mimetypes.guess_type(ebook.cover.name or '')[0] or 'image/jpeg'
        return self._stream(ebook.cover, content_type)

    @action(detail=True, methods=['post'])
    def tracking(self, request, pk=None):
        """
        Answer the "track progress for this book?" question.
        Body: {enabled: bool, book?: catalog book id, pages?: page count of the print edition}
        """
        ebook = self.get_object()
        if not request.data.get('enabled'):
            ebook.track_progress = False
            ebook.save(update_fields=['track_progress', 'updated_at'])
            return Response(EBookSerializer(ebook, context={'request': request}).data)

        book = None
        if request.data.get('book'):
            book = Book.objects.filter(pk=request.data['book']).first()
            if book is None:
                return Response({'book': ['Book not found.']}, status=status.HTTP_400_BAD_REQUEST)

        pages = request.data.get('pages')
        try:
            pages = int(pages) if pages else None
        except (TypeError, ValueError):
            pages = None
        if pages is not None and not 1 <= pages <= 20000:
            pages = None

        ebook_progress.enable_tracking(ebook, book=book, pages=pages)
        ebook.refresh_from_db()
        return Response(EBookSerializer(ebook, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='link-catalog')
    def link_catalog(self, request, pk=None):
        """Make sure the file is linked to a catalog book (needed for quotes/notes/words made in the reader)."""
        ebook = self.get_object()
        if not ebook.book_id:
            ebook.book = ebook_progress.find_or_create_catalog_book(ebook)
            ebook.save(update_fields=['book', 'updated_at'])
        return Response(EBookSerializer(ebook, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        """Mark the linked library book as read."""
        ebook = self.get_object()
        if not ebook.track_progress or not ebook.book_id:
            return Response({'detail': 'Progress tracking is off for this e-book.'}, status=status.HTTP_400_BAD_REQUEST)
        ebook_progress.finish(ebook)
        return Response(EBookSerializer(ebook, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def session(self, request, pk=None):
        """Log a reading session: {duration_seconds, start_progress, end_progress}."""
        ebook = self.get_object()
        try:
            duration = min(int(request.data.get('duration_seconds', 0)), 12 * 3600)
            start = float(request.data.get('start_progress') or 0)
            end = float(request.data.get('end_progress') or start)
        except (TypeError, ValueError):
            return Response({'detail': 'Invalid session data.'}, status=status.HTTP_400_BAD_REQUEST)
        clamp = lambda v: min(max(v, 0.0), 1.0)
        session = ebook_progress.record_session(ebook, duration, clamp(start), clamp(end))
        return Response({'logged': session is not None})

    @action(detail=False, methods=['get'], url_path='public-domain/search')
    def public_domain_search(self, request):
        """Search free public-domain classics (Project Gutenberg). Params: q, language, page."""
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1
        query = request.query_params.get('q', '').strip()[:200]
        language = request.query_params.get('language', '').strip()[:20]
        try:
            data = public_domain.search(query, language, page)
        except public_domain.CatalogUnavailable:
            return Response(
                {'detail': 'The public-domain catalog is not responding right now. Try again in a moment.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        owned = dict(
            EBook.objects
            .filter(user=request.user, source=EBook.SOURCE_GUTENBERG)
            .values_list('source_id', 'id')
        )
        for item in data['results']:
            item['ebook_id'] = owned.get(str(item['id']))
        return Response(data)

    @action(detail=False, methods=['post'], url_path='public-domain/import')
    def public_domain_import(self, request):
        """Add a Gutenberg book to the user's e-books: {gutenberg_id}."""
        try:
            gutenberg_id = int(request.data.get('gutenberg_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'gutenberg_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = EBook.objects.filter(
            user=request.user, source=EBook.SOURCE_GUTENBERG, source_id=str(gutenberg_id)
        ).first()
        if existing:
            return Response(EBookSerializer(existing, context={'request': request}).data)

        try:
            meta = public_domain.get_book(gutenberg_id)
            if not meta['has_epub']:
                return Response({'detail': 'This title has no EPUB edition.'}, status=status.HTTP_400_BAD_REQUEST)
            content = public_domain.download_epub(gutenberg_id)
        except public_domain.CatalogUnavailable:
            return Response(
                {'detail': 'Could not download this book from Project Gutenberg. Try again in a moment.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        upload = ContentFile(content, name=f'gutenberg-{gutenberg_id}.epub')
        if detect_format(upload) != EBook.FORMAT_EPUB:
            return Response({'detail': 'The downloaded file is not a valid EPUB.'}, status=status.HTTP_502_BAD_GATEWAY)

        used = EBook.objects.filter(user=request.user).aggregate(total=Sum('file_size'))['total'] or 0
        if used + upload.size > settings.EBOOK_USER_QUOTA_MB * 1024 * 1024:
            return Response({'detail': 'Storage limit reached. Delete some e-books first.'}, status=status.HTTP_400_BAD_REQUEST)

        ebook = EBook(
            user=request.user,
            title=(meta['title'] or f'Gutenberg #{gutenberg_id}')[:500],
            author=(', '.join(meta['authors']) or 'Unknown')[:500],
            language=(meta['languages'][0] if meta['languages'] else '')[:20],
            format=EBook.FORMAT_EPUB,
            file_size=upload.size,
            original_filename=upload.name,
            source=EBook.SOURCE_GUTENBERG,
            source_id=str(gutenberg_id),
        )
        ebook.file.save(upload.name, upload, save=False)
        cover = public_domain.download_cover(meta['cover_url'])
        if cover:
            ebook.cover.save(f'gutenberg-{gutenberg_id}.jpg', ContentFile(cover), save=False)
        ebook.save()
        return Response(EBookSerializer(ebook, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def usage(self, request):
        used = EBook.objects.filter(user=request.user).aggregate(total=Sum('file_size'))['total'] or 0
        return Response({
            'used_bytes': used,
            'quota_bytes': settings.EBOOK_USER_QUOTA_MB * 1024 * 1024,
            'max_upload_bytes': settings.EBOOK_MAX_UPLOAD_MB * 1024 * 1024,
        })
