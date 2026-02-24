from django.utils import timezone


# Base points for each action type
POINTS_TABLE = {
    # Content creation
    'quote_added': ('content', 2),
    'vocabulary_added': ('content', 1),
    'study_note_added': ('content', 1),
    'review_written': ('content', 5),
    'reading_list_created': ('content', 3),
    'book_imported': ('content', 6),
    'book_added_manual': ('content', 10),
    'dna_vote_cast': ('community', 4),
    # Community
    'circle_post_created': ('community', 2),
    'discussion_created': ('community', 3),
    'topic_message_posted': ('community', 1),
    # Curation
    'author_linked': ('curation', 3),
    'author_unlinked': ('curation', 3),
    'author_bio_added': ('curation', 5),
    'author_pair_dismissed': ('curation', 1),
    'book_metadata_edited': ('curation', 4),
    'data_issue_resolved': ('curation', 5),
    'books_linked': ('curation', 3),
    'book_pair_dismissed': ('curation', 1),
    # Reading
    'book_finished': ('reading', 3),
    'challenge_completed': ('reading', 5),
}


def get_quality_multiplier(quality_ratio):
    """Quality multiplier based on user's historical accuracy."""
    if quality_ratio >= 0.95:
        return 1.2
    elif quality_ratio >= 0.80:
        return 1.0
    elif quality_ratio >= 0.60:
        return 0.7
    else:
        return 0.3


def calculate_diminishing_points(user, action, base_points):
    """
    Apply diminishing returns for repeated same-action contributions in a day.
    Prevents gaming via mass low-effort contributions.
    """
    from apps.contributions.models import ContributionLog

    today_count = ContributionLog.objects.filter(
        user=user, action=action,
        created_at__date=timezone.now().date()
    ).count()

    if today_count < 10:
        return base_points
    elif today_count < 25:
        return max(1, base_points // 2)
    else:
        return 1


def calculate_awarded_points(user, action):
    """
    Calculate final awarded points for an action, applying
    diminishing returns and quality multiplier.
    Returns (category, base_points, awarded_points).
    """
    if action not in POINTS_TABLE:
        return 'content', 0, 0

    category, base_points = POINTS_TABLE[action]

    # Apply diminishing returns
    after_diminish = calculate_diminishing_points(user, action, base_points)

    # Apply quality multiplier
    try:
        quality_ratio = user.reputation.quality_ratio
    except Exception:
        quality_ratio = 1.0

    multiplier = get_quality_multiplier(quality_ratio)
    awarded = max(1, int(after_diminish * multiplier))

    return category, base_points, awarded
