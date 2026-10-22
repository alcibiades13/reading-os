from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.ebooks.models import EBookAnnotation
from apps.reading.models import Quote, VocabularyWord
from apps.reading.models_study import StudyNote


def _remove_annotation(kind):
    def handler(sender, instance, **kwargs):
        EBookAnnotation.objects.filter(kind=kind, object_id=instance.pk).delete()
    return handler


# Deleting a quote/note/word removes its highlight from the e-book
post_delete.connect(_remove_annotation(EBookAnnotation.KIND_QUOTE), sender=Quote, weak=False, dispatch_uid='ebook_annotation_quote')
post_delete.connect(_remove_annotation(EBookAnnotation.KIND_NOTE), sender=StudyNote, weak=False, dispatch_uid='ebook_annotation_note')
post_delete.connect(_remove_annotation(EBookAnnotation.KIND_WORD), sender=VocabularyWord, weak=False, dispatch_uid='ebook_annotation_word')
