from django.db import models
from rest_framework import viewsets, filters, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.codex.models import JournalEntry, Manuscript, Chapter
from apps.codex.serializers import (
    JournalEntrySerializer,
    ManuscriptListSerializer,
    ManuscriptDetailSerializer,
    ManuscriptCreateSerializer,
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
        """Filter queryset by current user"""
        return JournalEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user on create"""
        serializer.save(user=self.request.user)


class ManuscriptViewSet(viewsets.ModelViewSet):
    """ViewSet for Manuscript model"""
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle', 'genre']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ManuscriptCreateSerializer
        elif self.action == 'retrieve':
            return ManuscriptDetailSerializer
        return ManuscriptListSerializer

    def get_queryset(self):
        """Filter queryset by current user"""
        return Manuscript.objects.filter(user=self.request.user).prefetch_related('chapters')

    def perform_create(self, serializer):
        """Set user on create"""
        serializer.save(user=self.request.user)

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


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for Chapter model"""
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter chapters by manuscript owner"""
        return Chapter.objects.filter(manuscript__user=self.request.user)

    def perform_create(self, serializer):
        """Ensure user owns the manuscript"""
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
