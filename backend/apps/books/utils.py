from collections import defaultdict
from apps.books.models import Author, Book, BookDNA, BookGroupDNA


def compute_similar_authors(author, limit=5):
    """
    Find authors whose books share similar DNA themes with this author's books.
    Uses bulk queries instead of per-author iteration.
    """
    # Get all author IDs (including aliases)
    if author.author_group_id:
        alias_ids = set(author.author_group.members.values_list('id', flat=True))
    else:
        alias_ids = {author.id}

    # Get this author's book IDs
    author_book_ids = set(
        Book.objects.filter(authors__id__in=alias_ids)
        .values_list('id', flat=True)
    )
    if not author_book_ids:
        return []

    # Get group IDs for this author's books
    author_group_ids = set(
        Book.objects.filter(id__in=author_book_ids, book_group_id__isnull=False)
        .values_list('book_group_id', flat=True)
    )

    # Gather this author's themes from DNA (bulk: 2 queries max)
    author_themes = set()
    author_genre_tags = set()

    for gdna in BookGroupDNA.objects.filter(book_group_id__in=author_group_ids):
        author_themes.update(gdna.themes or [])
        author_themes.update(gdna.primary_themes or [])
        author_genre_tags.update(gdna.genre_tags or [])

    for bdna in BookDNA.objects.filter(book_id__in=author_book_ids):
        author_themes.update(bdna.themes or [])
        author_themes.update(bdna.primary_themes or [])
        author_genre_tags.update(bdna.genre_tags or [])

    if not author_themes and not author_genre_tags:
        return []

    # Build index: author_id → (themes, genre_tags) from ALL DNA records
    # This is 2 bulk queries instead of N*M individual queries
    book_to_authors = defaultdict(set)
    for book_id, author_id in (
        Book.authors.through.objects
        .exclude(author_id__in=alias_ids)
        .values_list('book_id', 'author_id')
    ):
        book_to_authors[book_id].add(author_id)

    author_theme_index = defaultdict(set)
    author_genre_tag_index = defaultdict(set)

    # From BookGroupDNA → map to books → map to authors
    group_to_books = defaultdict(set)
    for book_id, group_id in (
        Book.objects.filter(book_group_id__isnull=False)
        .exclude(id__in=author_book_ids)
        .values_list('id', 'book_group_id')
    ):
        group_to_books[group_id].add(book_id)

    for gdna in BookGroupDNA.objects.all():
        themes = set(gdna.themes or []) | set(gdna.primary_themes or [])
        gtags = set(gdna.genre_tags or [])
        if not themes and not gtags:
            continue
        for book_id in group_to_books.get(gdna.book_group_id, []):
            for aid in book_to_authors.get(book_id, []):
                author_theme_index[aid].update(themes)
                author_genre_tag_index[aid].update(gtags)

    # From BookDNA → map to authors
    for bdna in BookDNA.objects.exclude(book_id__in=author_book_ids):
        themes = set(bdna.themes or []) | set(bdna.primary_themes or [])
        gtags = set(bdna.genre_tags or [])
        if not themes and not gtags:
            continue
        for aid in book_to_authors.get(bdna.book_id, []):
            author_theme_index[aid].update(themes)
            author_genre_tag_index[aid].update(gtags)

    # Score candidates
    scored_ids = []
    for aid, other_themes in author_theme_index.items():
        if not other_themes:
            continue
        other_genre_tags = author_genre_tag_index.get(aid, set())

        theme_union = len(author_themes | other_themes)
        theme_sim = len(author_themes & other_themes) / theme_union if theme_union else 0

        genre_union = len(author_genre_tags | other_genre_tags)
        genre_sim = len(author_genre_tags & other_genre_tags) / genre_union if genre_union else 0

        combined = theme_sim * 0.7 + genre_sim * 0.3
        if combined > 0.15:
            scored_ids.append((aid, round(combined, 3)))

    scored_ids.sort(key=lambda x: x[1], reverse=True)
    top_ids = scored_ids[:limit]

    if not top_ids:
        return []

    # Fetch author objects in one query
    authors_map = {
        a.id: a for a in Author.objects.filter(id__in=[aid for aid, _ in top_ids])
    }

    return [
        {
            'id': aid,
            'name': authors_map[aid].name,
            'slug': authors_map[aid].slug,
            'photo': authors_map[aid].photo,
            'similarity': sim,
        }
        for aid, sim in top_ids if aid in authors_map
    ]
