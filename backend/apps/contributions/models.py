from django.conf import settings
from django.db import models
from django.utils import timezone


class ContributionLog(models.Model):
    """
    Immutable audit log of all contributable actions.
    Created via signals when users perform tracked actions.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='contributions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    ACTION_CHOICES = [
        # Content creation
        ('quote_added', 'Quote Added'),
        ('vocabulary_added', 'Vocabulary Added'),
        ('study_note_added', 'Study Note Added'),
        ('review_written', 'Review Written'),
        ('reading_list_created', 'List Created'),
        ('book_imported', 'Book Imported'),
        ('book_added_manual', 'Book Added Manually'),
        ('dna_vote_cast', 'DNA Vote Cast'),
        # Community
        ('circle_post_created', 'Circle Post'),
        ('discussion_created', 'Discussion Created'),
        ('topic_message_posted', 'Message Posted'),
        # Curation
        ('author_linked', 'Authors Linked'),
        ('author_unlinked', 'Author Unlinked'),
        ('author_bio_added', 'Author Bio Added'),
        ('author_pair_dismissed', 'Pair Dismissed'),
        ('book_metadata_edited', 'Book Edited'),
        ('data_issue_resolved', 'Issue Resolved'),
        ('books_linked', 'Books Linked'),
        ('book_pair_dismissed', 'Book Pair Dismissed'),
        # Reading
        ('book_finished', 'Book Finished'),
        ('challenge_completed', 'Challenge Done'),
    ]
    action = models.CharField(max_length=40, choices=ACTION_CHOICES, db_index=True)

    # Polymorphic reference (same pattern as FeedItem)
    content_type = models.CharField(max_length=50)
    object_id = models.IntegerField()

    # Scoring
    CATEGORY_CHOICES = [
        ('content', 'Content Creation'),
        ('community', 'Community Participation'),
        ('curation', 'Data Curation'),
        ('reading', 'Reading Activity'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    base_points = models.IntegerField()
    awarded_points = models.IntegerField()

    # Revert support
    previous_state = models.JSONField(null=True, blank=True)
    is_reverted = models.BooleanField(default=False)
    reverted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reverted_contributions'
    )
    reverted_at = models.DateTimeField(null=True, blank=True)

    # Quality
    QUALITY_CHOICES = [
        ('unreviewed', 'Unreviewed'),
        ('approved', 'Approved'),
        ('flagged', 'Flagged'),
        ('rejected', 'Rejected'),
    ]
    quality_status = models.CharField(
        max_length=12, choices=QUALITY_CHOICES, default='unreviewed'
    )

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['quality_status']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user} — {self.get_action_display()} ({self.awarded_points}pts)"


class UserReputation(models.Model):
    """
    Denormalized reputation summary. Updated via signals when
    ContributionLog entries are created.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reputation'
    )

    # Points by category
    content_points = models.IntegerField(default=0)
    community_points = models.IntegerField(default=0)
    curation_points = models.IntegerField(default=0)
    reading_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0, db_index=True)

    # Counts
    total_contributions = models.IntegerField(default=0)

    # Quality
    approved_count = models.IntegerField(default=0)
    flagged_count = models.IntegerField(default=0)
    rejected_count = models.IntegerField(default=0)
    quality_ratio = models.FloatField(default=1.0)

    # Tier
    TIER_CHOICES = [
        ('reader', 'Reader'),
        ('contributor', 'Contributor'),
        ('curator', 'Curator'),
        ('moderator', 'Moderator'),
    ]
    tier = models.CharField(max_length=12, choices=TIER_CHOICES, default='reader')
    tier_updated_at = models.DateTimeField(null=True, blank=True)
    is_tier_locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TIER_ORDER = ['reader', 'contributor', 'curator', 'moderator']

    class Meta:
        ordering = ['-total_points']

    def __str__(self):
        return f"{self.user} — {self.get_tier_display()} ({self.total_points}pts)"

    @property
    def next_tier(self):
        idx = self.TIER_ORDER.index(self.tier)
        if idx < len(self.TIER_ORDER) - 1:
            return self.TIER_ORDER[idx + 1]
        return None

    @property
    def next_tier_points_needed(self):
        thresholds = {'reader': 50, 'contributor': 500, 'curator': None}
        return thresholds.get(self.tier)

    def check_and_update_tier(self):
        """Auto-promote if requirements are met. Never auto-demotes."""
        if self.is_tier_locked:
            return

        current_rank = self.TIER_ORDER.index(self.tier)

        # Check Curator (rank 2)
        if current_rank < 2:
            curation_count = ContributionLog.objects.filter(
                user=self.user, category='curation'
            ).count()
            if (self.total_points >= 500
                    and curation_count >= 10
                    and self.quality_ratio >= 0.8):
                self.tier = 'curator'
                self.tier_updated_at = timezone.now()
                self.save()
                return

        # Check Contributor (rank 1)
        if current_rank < 1:
            distinct_cats = ContributionLog.objects.filter(
                user=self.user
            ).values('category').distinct().count()
            if (self.total_points >= 50
                    and self.total_contributions >= 5
                    and distinct_cats >= 2):
                self.tier = 'contributor'
                self.tier_updated_at = timezone.now()
                self.save()


class Badge(models.Model):
    """Badge template / definition."""
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')

    CATEGORY_CHOICES = [
        ('activity', 'Activity'),
        ('quality', 'Quality'),
        ('special', 'Special'),
        ('founding', 'Founding'),
    ]
    category = models.CharField(max_length=12, choices=CATEGORY_CHOICES)

    # Auto-award criteria (null = manual only)
    auto_criteria = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """A badge awarded to a user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='earned_badges'
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awards')
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='awarded_badges'
    )

    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-awarded_at']

    def __str__(self):
        return f"{self.user} — {self.badge.name}"


class ContributionFlag(models.Model):
    """Flag a contribution as problematic."""
    contribution = models.ForeignKey(
        ContributionLog, on_delete=models.CASCADE, related_name='flags'
    )
    flagged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='flagged_contributions'
    )
    reason = models.CharField(max_length=200)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='resolved_flags'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Flag on {self.contribution} by {self.flagged_by}"
