from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.lists.models import ReadingList, ReadingListItem
from apps.lists.serializers import (
    ReadingListListSerializer,
    ReadingListDetailSerializer,
    ReadingListCreateSerializer,
    ReadingListItemSerializer,
    ReadingListItemCreateSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Check if list is public or user is owner
            return obj.is_public or obj.user == request.user
        
        # Write permissions only to owner
        return obj.user == request.user


class ReadingListViewSet(viewsets.ModelViewSet):
    """ViewSet for ReadingList model"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReadingListCreateSerializer
        elif self.action == 'retrieve':
            return ReadingListDetailSerializer
        return ReadingListListSerializer
    
    def get_queryset(self):
        """Filter queryset by user and visibility"""
        queryset = ReadingList.objects.all().prefetch_related('items__book')
        
        # Filter by current user or specific user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        else:
            # Default to current user's lists
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by public
        is_public = self.request.query_params.get('public', None)
        if is_public == 'true':
            queryset = queryset.filter(is_public=True)
        
        # Filter by smart lists
        is_smart = self.request.query_params.get('smart', None)
        if is_smart == 'true':
            queryset = queryset.filter(is_smart=True)
        elif is_smart == 'false':
            queryset = queryset.filter(is_smart=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_book(self, request, pk=None):
        """Add a book to this list"""
        reading_list = self.get_object()
        book_id = request.data.get('book_id')
        note = request.data.get('note', '')
        order = request.data.get('order', 0)
        
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if book already exists in list
        if ReadingListItem.objects.filter(
            reading_list=reading_list,
            book_id=book_id
        ).exists():
            return Response(
                {'error': 'Book already in list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create item
        item = ReadingListItem.objects.create(
            reading_list=reading_list,
            book_id=book_id,
            note=note,
            order=order
        )
        
        serializer = ReadingListItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_book(self, request, pk=None):
        """Remove a book from this list"""
        reading_list = self.get_object()
        book_id = request.data.get('book_id')
        
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = ReadingListItem.objects.get(
                reading_list=reading_list,
                book_id=book_id
            )
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ReadingListItem.DoesNotExist:
            return Response(
                {'error': 'Book not in list'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Reorder books in list"""
        reading_list = self.get_object()
        order_data = request.data.get('order', [])
        
        # order_data should be list of {book_id: X, order: Y}
        if not order_data:
            return Response(
                {'error': 'order data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for item_data in order_data:
            book_id = item_data.get('book_id')
            order = item_data.get('order')
            
            if book_id and order is not None:
                ReadingListItem.objects.filter(
                    reading_list=reading_list,
                    book_id=book_id
                ).update(order=order)
        
        serializer = ReadingListDetailSerializer(reading_list)
        return Response(serializer.data)


class ReadingListItemViewSet(viewsets.ModelViewSet):
    """ViewSet for ReadingListItem model"""
    serializer_class = ReadingListItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter to items from current user's lists"""
        return ReadingListItem.objects.filter(
            reading_list__user=self.request.user
        ).select_related('reading_list', 'book').prefetch_related('book__authors')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReadingListItemCreateSerializer
        return ReadingListItemSerializer

