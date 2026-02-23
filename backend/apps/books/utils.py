from apps.books.models import Author, Book


def compute_similar_authors(author, limit=5):
    """
    Find authors whose books share similar DNA themes with this author's books.
    Used for the "Similar Minds" sidebar widget on the author page.
    """
    # Get all author IDs (including aliases)
    if author.author_group_id:
        alias_ids = list(author.author_group.members.values_list('id', flat=True))
    else:
        alias_ids = [author.id]

    author_books = Book.objects.filter(
        authors__id__in=alias_ids
    ).distinct().select_related('book_group')

    if not author_books.exists():
        return []

    # Gather themes from this author's books' DNA
    author_themes = set()
    author_genre_tags = set()

    for book in author_books:
        dna = book.effective_dna
        if dna:
            author_themes.update(dna.themes or [])
            author_themes.update(dna.primary_themes or [])
            author_genre_tags.update(dna.genre_tags or [])

    if not author_themes and not author_genre_tags:
        return []

    # Find other authors whose books share themes
    other_authors = Author.objects.exclude(id__in=alias_ids).prefetch_related('books')

    scored = []
    for other in other_authors:
        other_book_list = list(other.books.all()[:10])
        if not other_book_list:
            continue

        other_themes = set()
        other_genre_tags = set()
        for book in other_book_list:
            dna = book.effective_dna
            if dna:
                other_themes.update(dna.themes or [])
                other_themes.update(dna.primary_themes or [])
                other_genre_tags.update(dna.genre_tags or [])

        if not other_themes:
            continue

        # Jaccard similarity on themes
        theme_union = len(author_themes | other_themes)
        theme_sim = len(author_themes & other_themes) / theme_union if theme_union > 0 else 0

        # Genre tag overlap bonus
        genre_union = len(author_genre_tags | other_genre_tags)
        genre_sim = len(author_genre_tags & other_genre_tags) / genre_union if genre_union > 0 else 0

        combined = theme_sim * 0.7 + genre_sim * 0.3

        if combined > 0.15:
            scored.append({
                'id': other.id,
                'name': other.name,
                'slug': other.slug,
                'photo': other.photo,
                'similarity': round(combined, 3),
            })

    scored.sort(key=lambda x: x['similarity'], reverse=True)
    return scored[:limit]
