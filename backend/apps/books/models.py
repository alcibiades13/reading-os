from django.db import models
from django.utils.text import slugify


class Author(models.Model):
    """Book author"""
    name = models.CharField(max_length=200, unique=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    photo = models.URLField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
    
    def __str__(self):
        return self.name


class Publisher(models.Model):
    """Book publisher"""
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Publisher'
        verbose_name_plural = 'Publishers'
    
    def __str__(self):
        return self.name


class Genre(models.Model):
    """Book genre (hierarchical)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subgenres'
    )
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    """Book tag for categorization"""
    CATEGORY_CHOICES = [
        ('mood', 'Mood'),
        ('theme', 'Theme'),
        ('style', 'Style'),
        ('topic', 'Topic'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class BookGroup(models.Model):
    """
    Represents a logical/abstract book that groups multiple editions.
    Example: "The Tunnel" by Sabato has Spanish edition, Serbian edition, etc.
    Different editions may have different ISBNs, publishers, languages, page counts,
    but they represent the same literary work.
    """
    # Canonical information (from best/first edition)
    canonical_title = models.CharField(max_length=500)
    canonical_authors = models.ManyToManyField(Author, related_name='book_groups')

    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Best/longest description from editions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats (denormalized for performance)
    editions_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['canonical_title']
        verbose_name = 'Book Group'
        verbose_name_plural = 'Book Groups'

    def __str__(self):
        try:
            authors = ", ".join([a.name for a in self.canonical_authors.all()[:2]])
            if self.canonical_authors.count() > 2:
                authors += "..."
            return f"{self.canonical_title} - {authors}" if authors else self.canonical_title
        except:
            return self.canonical_title

    def update_stats(self):
        """Update denormalized stats"""
        self.editions_count = self.editions.count()
        self.save()

    def get_primary_edition(self):
        """Get the primary edition, or first edition if none marked"""
        return self.editions.filter(is_primary_edition=True).first() or \
               self.editions.order_by('created_at').first()

    def get_or_create_dna(self):
        """Get DNA for this group, create default if doesn't exist"""
        dna, created = BookGroupDNA.objects.get_or_create(
            book_group=self,
            defaults={'source': 'manual'}
        )
        return dna


class BookGroupDNA(models.Model):
    """
    DNA vector for book groups - characteristics of the work itself.
    Moved from individual Book model to represent the work, not specific editions.
    All attributes use 0.0 - 1.0 scale.
    """
    book_group = models.OneToOneField(
        BookGroup,
        on_delete=models.CASCADE,
        related_name='dna'
    )

    # Core attributes (0.0 - 1.0 scale) - SAME AS OLD BookDNA
    pace = models.FloatField(
        default=0.5,
        help_text="0=slow/contemplative, 1=fast/page-turner"
    )
    complexity = models.FloatField(
        default=0.5,
        help_text="0=simple/accessible, 1=dense/challenging"
    )
    emotional_intensity = models.FloatField(
        default=0.5,
        help_text="0=light/easy, 1=heavy/intense"
    )
    darkness = models.FloatField(
        default=0.5,
        help_text="0=hopeful/light, 1=dark/bleak"
    )
    character_focus = models.FloatField(
        default=0.5,
        help_text="0=plot-driven, 1=character-driven"
    )
    introspection = models.FloatField(
        default=0.5,
        help_text="0=action/external, 1=introspective/philosophical"
    )

    # Themes (list of theme slugs)
    themes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of theme slugs: ['faith', 'identity', 'suffering']"
    )

    # Meta
    SOURCE_CHOICES = [
        ('user_votes', 'User Votes Aggregated'),
        ('ai_generated', 'AI Generated'),
        ('manual', 'Manual Entry'),
        ('migrated', 'Migrated from Book'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual'
    )
    vote_count = models.IntegerField(
        default=0,
        help_text="Number of user votes for these attributes"
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="0-1, confidence in these values based on vote count"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Book Group DNA'
        verbose_name_plural = 'Book Group DNAs'

    def __str__(self):
        return f"DNA: {self.book_group.canonical_title}"

    def to_vector(self):
        """Convert to list for similarity calculation"""
        return [
            self.pace,
            self.complexity,
            self.emotional_intensity,
            self.darkness,
            self.character_focus,
            self.introspection,
        ]


class Book(models.Model):
    """
    Central Book model.
    Books can be added manually or via ISBN lookup (Google Books, Open Library).
    """
    # Basic info
    isbn = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        help_text="ISBN-10 or ISBN-13"
    )
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=550, blank=True, db_index=True)
    subtitle = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    
    # Relationships
    authors = models.ManyToManyField(
        Author,
        related_name='books',
        blank=True
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='books'
    )
    
    # Publishing details
    published_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=10, default='sr')
    pages = models.IntegerField(null=True, blank=True)
    
    # Visual
    cover_image = models.URLField(
        blank=True,
        help_text="URL to cover image"
    )
    
    # Categorization
    genres = models.ManyToManyField(
        Genre,
        related_name='books',
        blank=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='books',
        blank=True
    )
    
    # Source tracking (important for your scraping strategy)
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('google_books', 'Google Books API'),
        ('open_library', 'Open Library API'),
        ('delfi_scrape', 'Delfi Scrape'),
        ('vulkan_scrape', 'Vulkan Scrape'),
        ('laguna_scrape', 'Laguna Scrape'),
    ]
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='manual'
    )
    external_ids = models.JSONField(
        default=dict,
        blank=True,
        help_text="External IDs: {'goodreads_id': '...', 'google_id': '...'}"
    )

    # Edition/Version Management
    book_group = models.ForeignKey(
        'BookGroup',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='editions',
        help_text="Group linking different editions of the same work"
    )
    is_primary_edition = models.BooleanField(
        default=False,
        help_text="Primary edition for this book group"
    )

    # Featured/Curation
    is_featured = models.BooleanField(
        default=False,
        help_text="Mark as featured book for cold start/discovery"
    )
    featured_order = models.IntegerField(
        default=0,
        help_text="Order for featured books (lower = higher priority)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['title']),
        ]
    
    def __str__(self):
        try:
            authors_str = ", ".join([a.name for a in self.authors.all()[:2]])
            if self.authors.count() > 2:
                authors_str += "..."
            return f"{self.title} - {authors_str}" if authors_str else self.title
        except:
            return self.title
    
    @property
    def author_names(self):
        """Returns comma-separated author names"""
        return ", ".join([a.name for a in self.authors.all()])

    def get_other_editions(self):
        """Get all other editions in this book group"""
        if not self.book_group:
            return Book.objects.none()
        return self.book_group.editions.exclude(id=self.id)

    def has_other_editions(self):
        """Check if this book has other editions"""
        return self.book_group and self.book_group.editions.count() > 1

    @property
    def effective_dna(self):
        """
        Get DNA from BookGroup if available, else from Book (legacy).
        This provides backward compatibility during migration.
        """
        if self.book_group:
            try:
                return self.book_group.dna
            except:
                pass

        # Fallback to old BookDNA if exists
        try:
            return self.dna
        except:
            return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            # Ensure slug is not empty (for non-ASCII titles that don't slugify well)
            if not base_slug:
                base_slug = f"book-{self.pk or 'new'}"
            self.slug = base_slug
        super().save(*args, **kwargs)


class BookDNA(models.Model):
    """
    DNA vector for books - numerical attributes for recommendations.
    All attributes use 0.0 - 1.0 scale.
    """
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name='dna'
    )

    # Core attributes (0.0 - 1.0 scale)
    pace = models.FloatField(
        default=0.5,
        help_text="0=slow/contemplative, 1=fast/page-turner"
    )
    complexity = models.FloatField(
        default=0.5,
        help_text="0=simple/accessible, 1=dense/challenging"
    )
    emotional_intensity = models.FloatField(
        default=0.5,
        help_text="0=light/easy, 1=heavy/intense"
    )
    darkness = models.FloatField(
        default=0.5,
        help_text="0=hopeful/light, 1=dark/bleak"
    )
    character_focus = models.FloatField(
        default=0.5,
        help_text="0=plot-driven, 1=character-driven"
    )
    introspection = models.FloatField(
        default=0.5,
        help_text="0=action/external, 1=introspective/philosophical"
    )

    # Themes (list of theme slugs)
    themes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of theme slugs: ['faith', 'identity', 'suffering']"
    )

    # Meta
    SOURCE_CHOICES = [
        ('user_votes', 'User Votes Aggregated'),
        ('ai_generated', 'AI Generated'),
        ('manual', 'Manual Entry'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual'
    )
    vote_count = models.IntegerField(
        default=0,
        help_text="Number of user votes for these attributes"
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="0-1, confidence in these values based on vote count"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Book DNA'
        verbose_name_plural = 'Book DNAs'

    def __str__(self):
        return f"DNA: {self.book.title}"

    def to_vector(self):
        """Convert to list for similarity calculation"""
        return [
            self.pace,
            self.complexity,
            self.emotional_intensity,
            self.darkness,
            self.character_focus,
            self.introspection,
        ]


class BookDNAVote(models.Model):
    """
    Individual user vote for Book DNA attributes.
    Stored for transparency and re-calculation capability.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='book_dna_votes'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='dna_votes'
    )
    user_book = models.ForeignKey(
        'reading.UserBook',
        on_delete=models.CASCADE,
        related_name='dna_vote',
        null=True,
        blank=True
    )

    # Votes for each attribute (null = not answered)
    pace = models.FloatField(null=True, blank=True)
    complexity = models.FloatField(null=True, blank=True)
    emotional_intensity = models.FloatField(null=True, blank=True)
    darkness = models.FloatField(null=True, blank=True)
    character_focus = models.FloatField(null=True, blank=True)
    introspection = models.FloatField(null=True, blank=True)

    # Themes selected by user
    themes = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'book']
        verbose_name = 'Book DNA Vote'
        verbose_name_plural = 'Book DNA Votes'

    def __str__(self):
        return f"{self.user.email} vote for {self.book.title}"
