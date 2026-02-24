from django.db import models


class DismissedBookPair(models.Model):
    """
    Stores pairs of books that an admin has confirmed are NOT the same work.
    Prevents them from appearing as merge candidates again.
    """
    book1_id = models.IntegerField()
    book2_id = models.IntegerField()
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book1_id', 'book2_id')

    def save(self, *args, **kwargs):
        if self.book1_id > self.book2_id:
            self.book1_id, self.book2_id = self.book2_id, self.book1_id
        super().save(*args, **kwargs)

    @classmethod
    def is_dismissed(cls, id1, id2):
        a, b = sorted([id1, id2])
        return cls.objects.filter(book1_id=a, book2_id=b).exists()

    @classmethod
    def get_dismissed_set(cls):
        return {
            frozenset([d['book1_id'], d['book2_id']])
            for d in cls.objects.values('book1_id', 'book2_id')
        }


class DismissedAuthorPair(models.Model):
    """
    Stores pairs of authors that an admin has confirmed are NOT the same person.
    Prevents them from appearing as merge candidates again.
    """
    author1_id = models.IntegerField()
    author2_id = models.IntegerField()
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('author1_id', 'author2_id')

    def save(self, *args, **kwargs):
        # Always store with smaller ID first for consistent lookups
        if self.author1_id > self.author2_id:
            self.author1_id, self.author2_id = self.author2_id, self.author1_id
        super().save(*args, **kwargs)

    @classmethod
    def is_dismissed(cls, id1, id2):
        a, b = sorted([id1, id2])
        return cls.objects.filter(author1_id=a, author2_id=b).exists()

    @classmethod
    def get_dismissed_set(cls):
        """Returns a set of frozensets for fast lookup."""
        return {
            frozenset([d['author1_id'], d['author2_id']])
            for d in cls.objects.values('author1_id', 'author2_id')
        }
