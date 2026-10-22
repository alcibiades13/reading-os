import zipfile
from django.conf import settings
from django.db.models import Sum
from rest_framework import serializers

from apps.books.models import Book
from apps.ebooks.models import EBook, EBookBookmark
from apps.ebooks.progress import get_user_book, overall_progress, total_pages

MAX_COVER_BYTES = 2 * 1024 * 1024
ALLOWED_COVER_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


def detect_format(uploaded):
    """Identify the file by its content (magic bytes), not just its extension."""
    uploaded.seek(0)
    head = uploaded.read(5)
    uploaded.seek(0)

    if head.startswith(b'%PDF-'):
        return EBook.FORMAT_PDF

    if head.startswith(b'PK\x03\x04'):
        try:
            with zipfile.ZipFile(uploaded) as zf:
                if 'META-INF/container.xml' in zf.namelist():
                    return EBook.FORMAT_EPUB
        except zipfile.BadZipFile:
            pass
        finally:
            uploaded.seek(0)

    return None


class LinkedBookSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'slug', 'cover_image', 'pages', 'authors']

    def get_authors(self, obj):
        return [a.name for a in obj.authors.all()]


class EBookBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = EBookBookmark
        fields = ['id', 'label', 'position', 'progress', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name the sticker.')
        return value

    def validate_progress(self, value):
        return None if value is None else min(max(value, 0.0), 1.0)


class EBookSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), allow_null=True, required=False)
    book_detail = LinkedBookSerializer(source='book', read_only=True)
    has_cover = serializers.SerializerMethodField()
    library_entry = serializers.SerializerMethodField()
    total_pages = serializers.SerializerMethodField()
    bookmarks = EBookBookmarkSerializer(many=True, read_only=True)
    overall_progress = serializers.SerializerMethodField()

    class Meta:
        model = EBook
        fields = [
            'id', 'title', 'author', 'language', 'isbn',
            'book', 'book_detail', 'library_entry', 'total_pages',
            'format', 'file_size', 'original_filename', 'page_count', 'has_cover', 'source', 'source_id',
            'position', 'progress', 'overall_progress', 'bookmarks', 'track_progress', 'last_opened_at',
            'created_at', 'updated_at',
        ]
        # track_progress changes only through the `tracking` action (it has side effects,
        # and multipart uploads would otherwise coerce a missing boolean to False)
        read_only_fields = [
            'format', 'file_size', 'original_filename', 'page_count', 'track_progress',
            'source', 'source_id', 'last_opened_at', 'created_at', 'updated_at',
        ]

    def get_has_cover(self, obj):
        return bool(obj.cover)

    def get_library_entry(self, obj):
        user_book = get_user_book(obj)
        if not user_book:
            return None
        return {
            'id': user_book.id,
            'status': user_book.status,
            'current_page': user_book.current_page,
        }

    def get_total_pages(self, obj):
        return total_pages(obj)

    def get_overall_progress(self, obj):
        return overall_progress(obj)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Title is required.')
        return value

    def validate_author(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Author is required.')
        return value

    def validate_progress(self, value):
        return min(max(value, 0.0), 1.0)


class EBookUploadSerializer(EBookSerializer):
    file = serializers.FileField(write_only=True)
    cover_file = serializers.FileField(write_only=True, required=False)
    page_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    class Meta(EBookSerializer.Meta):
        fields = EBookSerializer.Meta.fields + ['file', 'cover_file']
        read_only_fields = [f for f in EBookSerializer.Meta.read_only_fields if f != 'page_count']

    def validate_file(self, uploaded):
        max_bytes = settings.EBOOK_MAX_UPLOAD_MB * 1024 * 1024
        if uploaded.size > max_bytes:
            raise serializers.ValidationError(f'File is too large (max {settings.EBOOK_MAX_UPLOAD_MB} MB).')

        fmt = detect_format(uploaded)
        if not fmt:
            raise serializers.ValidationError('Only EPUB and PDF files are supported.')

        user = self.context['request'].user
        used = EBook.objects.filter(user=user).aggregate(total=Sum('file_size'))['total'] or 0
        quota = settings.EBOOK_USER_QUOTA_MB * 1024 * 1024
        if used + uploaded.size > quota:
            raise serializers.ValidationError(
                f'Storage limit reached ({settings.EBOOK_USER_QUOTA_MB} MB). Delete some e-books first.'
            )

        uploaded.detected_format = fmt
        return uploaded

    def validate_cover_file(self, cover):
        if cover.size > MAX_COVER_BYTES or getattr(cover, 'content_type', '') not in ALLOWED_COVER_TYPES:
            # Cover is optional - silently drop anything unusable instead of failing the upload
            return None
        return cover

    def create(self, validated_data):
        from apps.ebooks.progress import publish_cover_to_book

        uploaded = validated_data.pop('file')
        cover = validated_data.pop('cover_file', None)

        ebook = EBook(
            **validated_data,
            format=uploaded.detected_format,
            file_size=uploaded.size,
            original_filename=uploaded.name[:255],
        )
        ebook.file.save(uploaded.name, uploaded, save=False)
        if cover:
            ebook.cover.save(cover.name or 'cover.jpg', cover, save=False)
        ebook.save()
        publish_cover_to_book(ebook)
        return ebook
