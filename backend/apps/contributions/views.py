from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_api.permissions import IsAdminUser
from apps.contributions.models import (
    ContributionLog, UserReputation, Badge, UserBadge, ContributionFlag,
)
from apps.contributions.permissions import IsModeratorOrAdmin
from apps.contributions.serializers import (
    UserReputationSerializer, PublicUserReputationSerializer,
    ContributionLogSerializer, UserBadgeSerializer, BadgeSerializer,
)


# ─── Public endpoints (authenticated user) ───

class MyReputationView(APIView):
    """Get current user's reputation, tier, and badges."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rep, _ = UserReputation.objects.get_or_create(user=request.user)
        return Response(UserReputationSerializer(rep).data)


class MyBadgesView(APIView):
    """Get all badges earned by the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        earned = UserBadge.objects.filter(
            user=request.user
        ).select_related('badge').order_by('-awarded_at')
        return Response(UserBadgeSerializer(earned, many=True).data)


class MyContributionsView(APIView):
    """Paginated list of the current user's contributions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        qs = ContributionLog.objects.filter(user=request.user)
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': ContributionLogSerializer(qs[start:end], many=True).data,
        })


class UserReputationPublicView(APIView):
    """Public reputation view for any user."""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            rep = UserReputation.objects.get(user_id=user_id)
        except UserReputation.DoesNotExist:
            return Response({
                'tier': 'reader', 'tier_display': 'Reader',
                'total_points': 0, 'total_contributions': 0,
                'badges': [],
            })
        return Response(PublicUserReputationSerializer(rep).data)


class ContributionLeaderboardView(APIView):
    """Top contributors by total points."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 50)
        reps = UserReputation.objects.filter(
            total_points__gt=0
        ).select_related('user').order_by('-total_points')[:limit]

        results = []
        for rep in reps:
            earned_badges = UserBadge.objects.filter(
                user=rep.user
            ).select_related('badge')[:3]
            results.append({
                'user_id': rep.user.id,
                'name': rep.user.full_name or rep.user.email,
                'avatar': rep.user.avatar.url if rep.user.avatar else None,
                'tier': rep.tier,
                'tier_display': rep.get_tier_display(),
                'total_points': rep.total_points,
                'total_contributions': rep.total_contributions,
                'badges': UserBadgeSerializer(earned_badges, many=True).data,
            })

        return Response(results)


# ─── Admin / Moderator endpoints ───

class ContributionDashboardView(APIView):
    """Contribution statistics for admin dashboard."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        total_all_time = ContributionLog.objects.count()
        total_this_week = ContributionLog.objects.filter(
            created_at__gte=week_ago
        ).count()
        active_this_week = ContributionLog.objects.filter(
            created_at__gte=week_ago
        ).values('user').distinct().count()
        flagged_pending = ContributionLog.objects.filter(
            quality_status='flagged'
        ).count()
        avg_quality = UserReputation.objects.filter(
            total_contributions__gt=0
        ).aggregate(avg=Avg('quality_ratio'))['avg'] or 1.0

        # Category breakdown
        category_agg = ContributionLog.objects.values('category').annotate(
            total=Sum('awarded_points')
        )
        category_breakdown = {
            item['category']: item['total'] or 0 for item in category_agg
        }

        # Top contributors
        top_reps = UserReputation.objects.filter(
            total_points__gt=0
        ).select_related('user').order_by('-total_points')[:10]
        top_contributors = []
        for rep in top_reps:
            top_contributors.append({
                'user_id': rep.user.id,
                'name': rep.user.full_name or rep.user.email,
                'avatar': rep.user.avatar.url if rep.user.avatar else None,
                'tier': rep.tier,
                'tier_display': rep.get_tier_display(),
                'total_points': rep.total_points,
                'total_contributions': rep.total_contributions,
                'content_points': rep.content_points,
                'community_points': rep.community_points,
                'curation_points': rep.curation_points,
                'reading_points': rep.reading_points,
            })

        # Recent contributions
        recent = ContributionLog.objects.select_related('user').order_by(
            '-created_at'
        )[:20]

        return Response({
            'total_contributions_all_time': total_all_time,
            'total_contributions_this_week': total_this_week,
            'active_contributors_this_week': active_this_week,
            'flagged_pending': flagged_pending,
            'average_quality': round(avg_quality, 3),
            'category_breakdown': category_breakdown,
            'top_contributors': top_contributors,
            'recent_contributions': ContributionLogSerializer(recent, many=True).data,
        })


class ContributionReviewQueueView(APIView):
    """Flagged and unreviewed curation contributions."""
    permission_classes = [IsModeratorOrAdmin]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        qs = ContributionLog.objects.filter(
            quality_status__in=['flagged', 'unreviewed'],
            category='curation',
        ).select_related('user').order_by('-created_at')
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': ContributionLogSerializer(qs[start:end], many=True).data,
        })


class ApproveContributionView(APIView):
    """Approve a contribution."""
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request, contribution_id):
        try:
            log = ContributionLog.objects.get(id=contribution_id)
        except ContributionLog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        log.quality_status = 'approved'
        log.save()

        # Update user quality stats
        rep, _ = UserReputation.objects.get_or_create(user=log.user)
        rep.approved_count += 1
        rep.quality_ratio = (
            rep.approved_count / max(1, rep.approved_count + rep.rejected_count)
        )
        rep.save()

        return Response({'success': True})


class RejectContributionView(APIView):
    """Reject a contribution and deduct points."""
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request, contribution_id):
        try:
            log = ContributionLog.objects.get(id=contribution_id)
        except ContributionLog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        log.quality_status = 'rejected'
        log.save()

        # Deduct points and update quality
        rep, _ = UserReputation.objects.get_or_create(user=log.user)
        category_field = f'{log.category}_points'
        setattr(rep, category_field,
                max(0, getattr(rep, category_field) - log.awarded_points))
        rep.total_points = max(0, rep.total_points - log.awarded_points)
        rep.rejected_count += 1
        rep.quality_ratio = (
            rep.approved_count / max(1, rep.approved_count + rep.rejected_count)
        )
        rep.save()

        return Response({'success': True})


class RevertContributionView(APIView):
    """Revert a curation contribution using stored previous_state."""
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request, contribution_id):
        try:
            log = ContributionLog.objects.get(id=contribution_id)
        except ContributionLog.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        if log.is_reverted:
            return Response({'error': 'Already reverted'}, status=400)
        if not log.previous_state:
            return Response({'error': 'No previous state available for revert'}, status=400)

        success = _execute_revert(log)
        if not success:
            return Response({'error': 'Revert failed'}, status=500)

        log.is_reverted = True
        log.reverted_at = timezone.now()
        log.reverted_by = request.user
        log.save()

        # Deduct points
        rep, _ = UserReputation.objects.get_or_create(user=log.user)
        category_field = f'{log.category}_points'
        setattr(rep, category_field,
                max(0, getattr(rep, category_field) - log.awarded_points))
        rep.total_points = max(0, rep.total_points - log.awarded_points)
        rep.save()

        return Response({'success': True})


def _execute_revert(log):
    """Dispatch revert based on action type and previous_state."""
    from apps.books.models import Author

    try:
        if log.action == 'author_linked' and log.content_type == 'Author':
            author = Author.objects.get(id=log.object_id)
            prev = log.previous_state
            author.author_group_id = prev.get('author_group_id')
            author.is_primary_alias = prev.get('is_primary_alias', False)
            author.save()
            return True

        if log.action == 'author_unlinked' and log.content_type == 'Author':
            author = Author.objects.get(id=log.object_id)
            prev = log.previous_state
            author.author_group_id = prev.get('author_group_id')
            author.is_primary_alias = prev.get('is_primary_alias', False)
            author.save()
            return True

    except Exception:
        return False

    return False


class AwardBadgeView(APIView):
    """Manually award a badge to a user."""
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        badge_slug = request.data.get('badge_slug')

        if not user_id or not badge_slug:
            return Response({'error': 'user_id and badge_slug required'}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
            badge = Badge.objects.get(slug=badge_slug)
        except (User.DoesNotExist, Badge.DoesNotExist):
            return Response({'error': 'User or badge not found'}, status=404)

        obj, created = UserBadge.objects.get_or_create(
            user=user, badge=badge,
            defaults={'awarded_by': request.user}
        )

        if not created:
            return Response({'error': 'Badge already awarded'}, status=400)

        return Response({
            'success': True,
            'badge': BadgeSerializer(badge).data,
        })


class AllBadgesView(APIView):
    """List all available badges."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        badges = Badge.objects.filter(is_active=True)
        return Response(BadgeSerializer(badges, many=True).data)
