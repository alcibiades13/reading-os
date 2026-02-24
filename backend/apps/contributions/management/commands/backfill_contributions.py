from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.contributions.models import ContributionLog, UserReputation
from apps.contributions.scoring import POINTS_TABLE
from apps.contributions.signals import _check_badge_awards

User = get_user_model()


class Command(BaseCommand):
    help = 'Backfill contributions for existing users based on their content'

    def handle(self, *args, **options):
        from apps.reading.models import Quote, VocabularyWord, UserBook
        from apps.lists.models import ReadingList
        from apps.social.models import CirclePost, DiscussionTopic, TopicMessage

        total_created = 0

        for user in User.objects.all():
            user_created = 0

            # Quotes
            for obj in Quote.objects.filter(user=user):
                if not self._exists(user, 'quote_added', 'Quote', obj.id):
                    self._create(user, 'quote_added', 'Quote', obj.id, obj.created_at)
                    user_created += 1

            # Vocabulary
            try:
                from apps.reading.models import VocabularyWord
                for obj in VocabularyWord.objects.filter(user=user):
                    if not self._exists(user, 'vocabulary_added', 'VocabularyWord', obj.id):
                        self._create(user, 'vocabulary_added', 'VocabularyWord', obj.id, obj.created_at)
                        user_created += 1
            except Exception:
                pass

            # Study Notes
            try:
                from apps.reading.models_study import StudyNote
                for obj in StudyNote.objects.filter(user=user):
                    if not self._exists(user, 'study_note_added', 'StudyNote', obj.id):
                        self._create(user, 'study_note_added', 'StudyNote', obj.id, obj.created_at)
                        user_created += 1
            except Exception:
                pass

            # Books finished
            for obj in UserBook.objects.filter(user=user, status='read'):
                if not self._exists(user, 'book_finished', 'UserBook', obj.id):
                    ts = obj.finished_at or obj.updated_at or obj.started_at
                    self._create(user, 'book_finished', 'UserBook', obj.id, ts)
                    user_created += 1

            # Reviews
            for obj in UserBook.objects.filter(user=user).exclude(review='').exclude(review__isnull=True):
                if not self._exists(user, 'review_written', 'UserBook', obj.id):
                    ts = obj.updated_at or obj.finished_at
                    self._create(user, 'review_written', 'UserBook', obj.id, ts)
                    user_created += 1

            # Reading lists
            for obj in ReadingList.objects.filter(user=user):
                if not self._exists(user, 'reading_list_created', 'ReadingList', obj.id):
                    self._create(user, 'reading_list_created', 'ReadingList', obj.id, obj.created_at)
                    user_created += 1

            # Circle posts
            for obj in CirclePost.objects.filter(author=user):
                if not self._exists(user, 'circle_post_created', 'CirclePost', obj.id):
                    self._create(user, 'circle_post_created', 'CirclePost', obj.id, obj.created_at)
                    user_created += 1

            # Discussion topics
            for obj in DiscussionTopic.objects.filter(creator=user):
                if not self._exists(user, 'discussion_created', 'DiscussionTopic', obj.id):
                    self._create(user, 'discussion_created', 'DiscussionTopic', obj.id, obj.created_at)
                    user_created += 1

            # Topic messages
            for obj in TopicMessage.objects.filter(author=user):
                if not self._exists(user, 'topic_message_posted', 'TopicMessage', obj.id):
                    self._create(user, 'topic_message_posted', 'TopicMessage', obj.id, obj.created_at)
                    user_created += 1

            # DNA votes
            try:
                from apps.books.models import BookDNAVote
                for obj in BookDNAVote.objects.filter(user=user):
                    if not self._exists(user, 'dna_vote_cast', 'BookDNAVote', obj.id):
                        self._create(user, 'dna_vote_cast', 'BookDNAVote', obj.id, obj.created_at)
                        user_created += 1
            except Exception:
                pass

            if user_created > 0:
                # Recompute reputation totals
                self._recompute_reputation(user)
                # Check badges
                _check_badge_awards(user)
                total_created += user_created
                self.stdout.write(f'  {user.email}: {user_created} contributions backfilled')

        self.stdout.write(
            self.style.SUCCESS(f'Backfill complete: {total_created} total contributions created')
        )

    def _exists(self, user, action, content_type, object_id):
        return ContributionLog.objects.filter(
            user=user, action=action,
            content_type=content_type, object_id=object_id
        ).exists()

    def _create(self, user, action, content_type, object_id, timestamp=None):
        if action not in POINTS_TABLE:
            return
        category, base_points = POINTS_TABLE[action]
        log = ContributionLog(
            user=user, action=action,
            content_type=content_type, object_id=object_id,
            category=category, base_points=base_points,
            awarded_points=base_points,  # No diminishing returns for backfill
        )
        log.save()
        if timestamp:
            # Override auto_now_add
            ContributionLog.objects.filter(id=log.id).update(created_at=timestamp)

    def _recompute_reputation(self, user):
        from django.db.models import Sum
        rep, _ = UserReputation.objects.get_or_create(user=user)

        agg = ContributionLog.objects.filter(user=user).values('category').annotate(
            total=Sum('awarded_points'),
        )
        rep.content_points = 0
        rep.community_points = 0
        rep.curation_points = 0
        rep.reading_points = 0
        for item in agg:
            setattr(rep, f"{item['category']}_points", item['total'] or 0)

        rep.total_points = (
            rep.content_points + rep.community_points +
            rep.curation_points + rep.reading_points
        )
        rep.total_contributions = ContributionLog.objects.filter(user=user).count()
        rep.save()
        rep.check_and_update_tier()
