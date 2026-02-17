import uuid
import json
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, filters, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.codex.models import JournalEntry, Manuscript, Chapter
from apps.codex.serializers import (
    JournalEntrySerializer,
    ManuscriptListSerializer,
    ManuscriptDetailSerializer,
    ManuscriptCreateSerializer,
    ManuscriptPublicSerializer,
    ChapterSerializer,
)


class IsOwner(permissions.BasePermission):
    """Custom permission to only allow owners to access their objects"""

    def has_object_permission(self, request, view, obj):
        # For Chapter, check manuscript owner
        if hasattr(obj, 'manuscript'):
            return obj.manuscript.user == request.user
        return obj.user == request.user


class JournalEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for JournalEntry model"""
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by current user (SoftDeleteManager excludes deleted)"""
        return JournalEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Prevent editing locked entries (except toggling is_locked itself)"""
        instance = self.get_object()
        if instance.is_locked:
            incoming_keys = set(serializer.validated_data.keys())
            if incoming_keys != {'is_locked'}:
                raise permissions.PermissionDenied("This entry is locked. Unlock it first to edit.")
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete (locked entries cannot be deleted)"""
        if instance.is_locked:
            raise permissions.PermissionDenied("This entry is locked and cannot be deleted.")
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    @action(detail=False, methods=['get'])
    def trash(self, request):
        """List soft-deleted journal entries"""
        deleted = JournalEntry.all_objects.filter(
            user=request.user, deleted_at__isnull=False
        ).order_by('-deleted_at')
        serializer = JournalEntrySerializer(deleted, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted journal entry"""
        try:
            entry = JournalEntry.all_objects.get(
                pk=pk, user=request.user, deleted_at__isnull=False
            )
        except JournalEntry.DoesNotExist:
            return Response({'error': 'Not found in trash'}, status=status.HTTP_404_NOT_FOUND)
        entry.deleted_at = None
        entry.save(update_fields=['deleted_at'])
        return Response(JournalEntrySerializer(entry).data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export all journal entries as JSON"""
        entries = self.get_queryset()
        serializer = JournalEntrySerializer(entries, many=True)
        data = json.dumps(serializer.data, indent=2, default=str, ensure_ascii=False)
        response = HttpResponse(data, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="journal_entries.json"'
        return response


class ManuscriptViewSet(viewsets.ModelViewSet):
    """ViewSet for Manuscript model"""
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle', 'genre']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ManuscriptCreateSerializer
        elif self.action == 'retrieve':
            return ManuscriptDetailSerializer
        return ManuscriptListSerializer

    def get_queryset(self):
        """Filter by current user (SoftDeleteManager excludes deleted)"""
        return Manuscript.objects.filter(user=self.request.user).prefetch_related('chapters')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete"""
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    @action(detail=True, methods=['post'])
    def add_chapter(self, request, pk=None):
        """Add a new chapter to the manuscript"""
        manuscript = self.get_object()
        max_order = manuscript.chapters.aggregate(max_order=models.Max('order'))['max_order'] or 0
        chapter = Chapter.objects.create(
            manuscript=manuscript,
            title=request.data.get('title', f'Chapter {max_order + 1}'),
            order=max_order + 1
        )
        return Response(ChapterSerializer(chapter).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def trash(self, request):
        """List soft-deleted manuscripts"""
        deleted = Manuscript.all_objects.filter(
            user=request.user, deleted_at__isnull=False
        ).order_by('-deleted_at')
        serializer = ManuscriptListSerializer(deleted, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted manuscript"""
        try:
            ms = Manuscript.all_objects.get(
                pk=pk, user=request.user, deleted_at__isnull=False
            )
        except Manuscript.DoesNotExist:
            return Response({'error': 'Not found in trash'}, status=status.HTTP_404_NOT_FOUND)
        ms.deleted_at = None
        ms.save(update_fields=['deleted_at'])
        return Response(ManuscriptDetailSerializer(ms).data)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export manuscript as TXT or printable HTML"""
        manuscript = self.get_object()
        fmt = request.query_params.get('format', 'txt')
        chapters = manuscript.chapters.all().order_by('order')

        if fmt == 'txt':
            content = f"{manuscript.title}\n"
            if manuscript.subtitle:
                content += f"{manuscript.subtitle}\n"
            content += f"\n{'=' * 40}\n\n"
            for ch in chapters:
                content += f"\n{ch.title}\n{'-' * len(ch.title)}\n\n{ch.content}\n\n"
            response = HttpResponse(content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{manuscript.title}.txt"'
            return response
        elif fmt == 'html':
            chapters_html = ''
            for idx, ch in enumerate(chapters):
                page_break = 'style="page-break-before: always;"' if idx > 0 else ''
                content_html = (ch.content or '').replace('\n', '<br>')
                chapters_html += f'''
                <div class="chapter" {page_break}>
                    <h2>{ch.title or f"Chapter {idx + 1}"}</h2>
                    <div class="chapter-content">{content_html}</div>
                </div>'''

            html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{manuscript.title}</title>
<style>
@page {{ margin: 25mm; }}
body {{ font-family: 'Georgia', 'Times New Roman', serif; font-size: 12pt; line-height: 1.8; color: #1a1a1a; margin: 0; padding: 0; }}
.title-page {{ text-align: center; padding-top: 30vh; page-break-after: always; }}
.title-page h1 {{ font-size: 28pt; margin-bottom: 8px; }}
.title-page .subtitle {{ font-size: 16pt; color: #666; font-style: italic; }}
.title-page .genre {{ font-size: 10pt; color: #999; margin-top: 24px; text-transform: uppercase; letter-spacing: 2px; }}
.title-page .word-count {{ font-size: 9pt; color: #aaa; margin-top: 8px; }}
h2 {{ font-size: 18pt; margin-bottom: 24px; page-break-after: avoid; }}
.chapter-content {{ white-space: pre-wrap; word-wrap: break-word; }}
</style>
</head>
<body>
<div class="title-page">
    <h1>{manuscript.title}</h1>
    {"<div class='subtitle'>" + manuscript.subtitle + "</div>" if manuscript.subtitle else ""}
    <div class="genre">{manuscript.genre}</div>
    <div class="word-count">{manuscript.current_word_count:,} words</div>
</div>
{chapters_html}
</body>
</html>'''
            return HttpResponse(html, content_type='text/html; charset=utf-8')
        else:
            return Response({'error': 'format must be txt or html'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_share(self, request, pk=None):
        """Toggle sharing and generate/revoke share token"""
        manuscript = self.get_object()
        if manuscript.is_shared:
            manuscript.is_shared = False
            manuscript.share_token = None
        else:
            manuscript.is_shared = True
            manuscript.share_token = uuid.uuid4()
        manuscript.save(update_fields=['is_shared', 'share_token'])
        return Response(ManuscriptDetailSerializer(manuscript).data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny],
            url_path='shared/(?P<token>[^/.]+)')
    def shared(self, request, token=None):
        """Public endpoint to view a shared manuscript"""
        try:
            manuscript = Manuscript.all_objects.get(
                share_token=token, is_shared=True, deleted_at__isnull=True
            )
        except Manuscript.DoesNotExist:
            return Response({'error': 'Manuscript not found or not shared'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ManuscriptPublicSerializer(manuscript).data)


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for Chapter model"""
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Chapter.objects.filter(manuscript__user=self.request.user)

    def perform_create(self, serializer):
        manuscript_id = self.request.data.get('manuscript')
        if manuscript_id:
            try:
                manuscript = Manuscript.objects.get(id=manuscript_id, user=self.request.user)
                max_order = manuscript.chapters.aggregate(max_order=models.Max('order'))['max_order'] or 0
                serializer.save(manuscript=manuscript, order=max_order + 1)
            except Manuscript.DoesNotExist:
                raise permissions.PermissionDenied("You don't own this manuscript")
        else:
            raise serializers.ValidationError({"manuscript": "This field is required"})
