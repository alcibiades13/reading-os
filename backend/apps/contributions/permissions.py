from rest_framework.permissions import BasePermission


class IsCuratorOrAdmin(BasePermission):
    """Allow curators, moderators, and staff."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.reputation.tier in ('curator', 'moderator')
        except Exception:
            return False


class IsModeratorOrAdmin(BasePermission):
    """Allow moderators and staff only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.reputation.tier == 'moderator'
        except Exception:
            return False
