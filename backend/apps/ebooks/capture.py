"""
Creating quotes / study notes / vocabulary words from text selected in the reader,
together with their position in the e-book, in one request (so the app can queue it
while offline and replay it safely later).
"""
from django.db import transaction
from rest_framework import serializers

from apps.ebooks import progress as ebook_progress
from apps.ebooks.models import EBookAnnotation
from apps.reading.models import Quote, VocabularyWord
from apps.reading.models_study import StudyNote
from apps.reading.serializers import QuoteCreateSerializer, QuoteDetailSerializer, VocabularyWordSerializer
from apps.reading.serializers_study import StudyNoteCreateSerializer, StudyNoteDetailSerializer

KINDS = {
    EBookAnnotation.KIND_QUOTE: (QuoteCreateSerializer, QuoteDetailSerializer, Quote),
    EBookAnnotation.KIND_NOTE: (StudyNoteCreateSerializer, StudyNoteDetailSerializer, StudyNote),
    EBookAnnotation.KIND_WORD: (VocabularyWordSerializer, VocabularyWordSerializer, VocabularyWord),
}


def _book_fields(ebook):
    book = ebook.book
    return {
        'book': book.id,
        'book_title': book.title or ebook.title,
        'book_author': ', '.join(a.name for a in book.authors.all()) or ebook.author,
    }


def capture(ebook, kind, data, position, text, client_id, request):
    """Returns (annotation, created)."""
    if kind not in KINDS:
        raise serializers.ValidationError({'kind': 'Unknown kind.'})

    if client_id:
        existing = ebook.annotations.filter(client_id=client_id).first()
        if existing:
            return existing, False

    # Quotes, notes and words belong to a catalog book
    if not ebook.book_id:
        ebook.book = ebook_progress.find_or_create_catalog_book(ebook)
        ebook.save(update_fields=['book', 'updated_at'])
        ebook_progress.publish_cover_to_book(ebook)

    create_serializer, _, _ = KINDS[kind]
    payload = {**data, **_book_fields(ebook)}
    if kind == EBookAnnotation.KIND_NOTE:
        payload = {k: v for k, v in payload.items() if k not in ('book_title', 'book_author')}
    if kind in (EBookAnnotation.KIND_QUOTE, EBookAnnotation.KIND_NOTE):
        user_book = ebook_progress.get_user_book(ebook)
        payload['user_book'] = user_book.id if user_book else None

    serializer = create_serializer(data=payload, context={'request': request})
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        obj = serializer.save(user=request.user)
        annotation = EBookAnnotation.objects.create(
            ebook=ebook,
            kind=kind,
            object_id=obj.pk,
            position=(position or '')[:1000],
            text=(text or '')[:5000],
            client_id=(client_id or '')[:64],
        )
    return annotation, True


def describe(annotations):
    """Annotations with a short summary of their quote/note/word (for the reader's highlight popover)."""
    by_kind = {}
    for annotation in annotations:
        by_kind.setdefault(annotation.kind, []).append(annotation.object_id)

    objects = {}
    for kind, ids in by_kind.items():
        _, _, model = KINDS[kind]
        for obj in model.objects.filter(pk__in=ids):
            objects[(kind, obj.pk)] = obj

    result = []
    for annotation in annotations:
        obj = objects.get((annotation.kind, annotation.object_id))
        if obj is None:
            continue  # object deleted (signal missed) - don't show a dead highlight
        if annotation.kind == EBookAnnotation.KIND_QUOTE:
            summary = {'title': 'Quote', 'body': obj.note or ''}
        elif annotation.kind == EBookAnnotation.KIND_NOTE:
            summary = {'title': obj.get_note_type_display(), 'body': obj.content, 'reference': obj.reference}
        else:
            summary = {'title': obj.word, 'body': obj.definition}
        result.append({
            'id': annotation.id,
            'kind': annotation.kind,
            'object_id': annotation.object_id,
            'position': annotation.position,
            'text': annotation.text,
            **summary,
        })
    return result
