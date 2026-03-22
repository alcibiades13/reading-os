from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.contributions.scoring import calculate_awarded_points


def create_contribution(user, action, content_type, object_id,
                        previous_state=None, metadata=None):
    """
    Create a ContributionLog entry and update UserReputation.
    Called from signals (auto) and views (curation actions).
    """
    from apps.contributions.models import ContributionLog, UserReputation, UserBadge, Badge

    category, base_points, awarded_points = calculate_awarded_points(user, action)

    log = ContributionLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        category=category,
        base_points=base_points,
        awarded_points=awarded_points,
        previous_state=previous_state,
        metadata=metadata or {},
    )

    # Atomic update of denormalized UserReputation using F() expressions
    rep, _ = UserReputation.objects.get_or_create(user=user)
    category_field = f'{category}_points'
    UserReputation.objects.filter(pk=rep.pk).update(
        **{category_field: F(category_field) + awarded_points},
        total_points=F('total_points') + awarded_points,
        total_contributions=F('total_contributions') + 1,
    )

    # Refresh from DB for tier check
    rep.refresh_from_db()
    rep.check_and_update_tier()

    # Check badge awards
    _check_badge_awards(user)

    return log


def _check_badge_awards(user):
    """Check and award any badges the user newly qualifies for."""
    from apps.contributions.models import ContributionLog, UserReputation, UserBadge, Badge

    already_earned = set(
        UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True)
    )

    for badge in Badge.objects.filter(is_active=True, auto_criteria__isnull=False):
        if badge.slug in already_earned:
            continue
        if _matches_criteria(user, badge.auto_criteria):
            UserBadge.objects.create(user=user, badge=badge)


def _matches_criteria(user, criteria):
    """Check if a user matches auto-award criteria."""
    from apps.contributions.models import ContributionLog, UserReputation

    # Action count criteria: {"action": "quote_added", "count": 100}
    if 'action' in criteria and 'count' in criteria:
        count = ContributionLog.objects.filter(
            user=user, action=criteria['action']
        ).count()
        return count >= criteria['count']

    # Tier criteria: {"tier": "curator"}
    if 'tier' in criteria:
        try:
            return user.reputation.tier == criteria['tier']
        except UserReputation.DoesNotExist:
            return False

    # Quality criteria: {"quality_ratio_min": 0.95, "min_contributions": 100}
    if 'quality_ratio_min' in criteria:
        try:
            rep = user.reputation
            return (rep.quality_ratio >= criteria['quality_ratio_min']
                    and rep.total_contributions >= criteria.get('min_contributions', 0))
        except UserReputation.DoesNotExist:
            return False

    return False


# ─── Auto-create UserReputation on User creation ───

User = None  # lazy import to avoid circular


def _get_user_model():
    global User
    if User is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    return User


@receiver(post_save, sender='users.User')
def create_user_reputation(sender, instance, created, **kwargs):
    """Create UserReputation when User is created."""
    if created:
        from apps.contributions.models import UserReputation
        UserReputation.objects.get_or_create(user=instance)


# ─── Content creation signals ───

@receiver(post_save, sender='reading.Quote')
def log_quote_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.user, 'quote_added', 'Quote', instance.id)


@receiver(post_save, sender='reading.VocabularyWord')
def log_vocabulary_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.user, 'vocabulary_added', 'VocabularyWord', instance.id)


@receiver(post_save, sender='reading.StudyNote')
def log_study_note_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.user, 'study_note_added', 'StudyNote', instance.id)


@receiver(post_save, sender='lists.ReadingList')
def log_reading_list_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.user, 'reading_list_created', 'ReadingList', instance.id)


@receiver(post_save, sender='books.BookDNAVote')
def log_dna_vote_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.user, 'dna_vote_cast', 'BookDNAVote', instance.id)


# ─── Community signals ───

@receiver(post_save, sender='social.CirclePost')
def log_circle_post_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.author, 'circle_post_created', 'CirclePost', instance.id)


@receiver(post_save, sender='social.DiscussionTopic')
def log_discussion_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.creator, 'discussion_created', 'DiscussionTopic', instance.id)


@receiver(post_save, sender='social.TopicMessage')
def log_topic_message_contribution(sender, instance, created, **kwargs):
    if created:
        create_contribution(instance.author, 'topic_message_posted', 'TopicMessage', instance.id)


# ─── Reading signals ───

@receiver(post_save, sender='reading.UserBook')
def log_book_finished_contribution(sender, instance, **kwargs):
    """Log when a user finishes a book (deduplicated)."""
    from apps.contributions.models import ContributionLog

    if instance.status != 'read' or not instance.finished_at:
        return

    already_logged = ContributionLog.objects.filter(
        user=instance.user, action='book_finished',
        content_type='UserBook', object_id=instance.id
    ).exists()

    if not already_logged:
        create_contribution(instance.user, 'book_finished', 'UserBook', instance.id)


@receiver(post_save, sender='reading.UserBook')
def log_review_contribution(sender, instance, **kwargs):
    """Log when a user writes a review (deduplicated)."""
    from apps.contributions.models import ContributionLog

    if not instance.review:
        return

    already_logged = ContributionLog.objects.filter(
        user=instance.user, action='review_written',
        content_type='UserBook', object_id=instance.id
    ).exists()

    if not already_logged:
        create_contribution(instance.user, 'review_written', 'UserBook', instance.id)
