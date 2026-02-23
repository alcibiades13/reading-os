"""
Author enrichment utility — fetches bio, photo, and dates from
Open Library, Wikipedia, and Wikidata.

Can be called directly for a single author or in bulk via management command.
"""

import re
import logging
import datetime
import unicodedata
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

HEADERS = {'User-Agent': 'ReadingOS/1.0 (book-tracker)'}
REQUEST_TIMEOUT = 15


def _normalize(text):
    """Strip accents and lowercase for comparison."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _validate_author_match(author_name, bio_text, page_title=''):
    """
    Check if the fetched bio/page actually refers to this author.
    Returns True if the result looks like a match, False otherwise.

    Heuristic: at least one significant name token (>= 3 chars) must appear
    in either the bio text or the Wikipedia page title (normalized, accent-free).
    """
    if not bio_text and not page_title:
        return False

    name_tokens = [
        _normalize(t) for t in author_name.split()
        if len(t) >= 3
    ]
    if not name_tokens:
        return True  # Very short name — can't validate, allow it

    haystack = _normalize(bio_text or '') + ' ' + _normalize(page_title or '')

    for token in name_tokens:
        if token in haystack:
            return True

    return False


def enrich_author(author, force=False):
    """
    Enrich a single Author instance with external data.
    Returns dict of fields that were updated, or empty dict if nothing changed.

    Pipeline:
      0. If grouped, try to copy data from primary alias first
      1. Open Library author search → OLID + wikidata QID
      2. Wikipedia REST API → bio + photo
      3. Wikidata → birth_date, death_date
      4. Fallback to Open Library for bio/photo
    """
    needs_bio = force or not author.bio
    needs_photo = force or not author.photo
    needs_dates = force or not author.birth_date

    if not needs_bio and not needs_photo and not needs_dates:
        return {}

    # Step 0: If author is in a group, copy from a sibling that has data
    group_data = _get_group_sibling_data(author)

    # Step 1: Open Library
    wikidata_qid = group_data.get('wikidata_id') or None
    ol_bio = ''
    ol_photo = ''

    # Use primary alias name for search if this author's name is a transliteration
    search_names = [author.name]
    if group_data.get('primary_name') and group_data['primary_name'] != author.name:
        search_names.append(group_data['primary_name'])

    for search_name in search_names:
        ol_data = _search_open_library(search_name)
        if ol_data:
            olid = ol_data.get('olid')
            if olid:
                ol_detail = _get_ol_author_detail(olid)
                if ol_detail:
                    bio_raw = ol_detail.get('bio')
                    candidate_bio = ''
                    if isinstance(bio_raw, dict):
                        candidate_bio = bio_raw.get('value', '')
                    elif isinstance(bio_raw, str):
                        candidate_bio = bio_raw

                    ol_name = ol_detail.get('name', '')
                    # Validate: OL result must match the author
                    if not _validate_author_match(author.name, candidate_bio, ol_name):
                        logger.debug(
                            f'OL result for "{search_name}" rejected — '
                            f'doesn\'t match author "{author.name}"'
                        )
                        continue

                    if not wikidata_qid:
                        wikidata_qid = (ol_detail.get('remote_ids') or {}).get('wikidata')
                    ol_bio = candidate_bio
                    photos = ol_detail.get('photos', [])
                    valid_photos = [p for p in photos if isinstance(p, int) and p > 0]
                    if valid_photos:
                        ol_photo = f'https://covers.openlibrary.org/a/id/{valid_photos[0]}-M.jpg'
                    elif olid:
                        ol_photo = f'https://covers.openlibrary.org/a/olid/{olid}-M.jpg'
                    if ol_bio:
                        break  # Good result, no need to try alternate name

    # Step 2: Wikipedia
    wiki_bio = ''
    wiki_photo = ''
    wiki_page_title = None
    wiki_from_qid = False  # Trust pages resolved via validated Wikidata QID

    if wikidata_qid:
        wiki_page_title = _get_wikipedia_title_from_wikidata(wikidata_qid)
        if wiki_page_title:
            wiki_from_qid = True
    if not wiki_page_title:
        # Try each name variant
        for search_name in search_names:
            wiki_page_title = _search_wikipedia(search_name)
            if wiki_page_title:
                break

    if wiki_page_title:
        wiki_data = _get_wikipedia_summary(wiki_page_title)
        if wiki_data:
            candidate_bio = wiki_data.get('extract', '')
            page_title_display = (wiki_page_title or '').replace('_', ' ')

            # Validate search-based results; QID-resolved pages are trusted
            if not wiki_from_qid and not _validate_author_match(
                author.name, candidate_bio, page_title_display
            ):
                logger.debug(
                    f'Wikipedia result "{wiki_page_title}" rejected — '
                    f'doesn\'t match author "{author.name}"'
                )
                # Reset — don't use this data
                wiki_page_title = None
            else:
                wiki_bio = candidate_bio
                thumb = wiki_data.get('thumbnail') or {}
                orig = wiki_data.get('originalimage') or {}
                wiki_photo = orig.get('source') or thumb.get('source') or ''
                if not wikidata_qid:
                    wikidata_qid = wiki_data.get('wikibase_item')

    # Step 3: Wikidata dates
    wd_birth = None
    wd_death = None
    if wikidata_qid and needs_dates:
        wd_birth, wd_death = _get_wikidata_dates(wikidata_qid)

    # Merge (Wikipedia preferred, OL fallback, group sibling last resort)
    new_bio = wiki_bio or ol_bio or group_data.get('bio', '')
    new_photo = wiki_photo or ol_photo or group_data.get('photo', '')

    # Apply updates
    updated_fields = {}

    if needs_bio and new_bio:
        author.bio = new_bio
        updated_fields['bio'] = new_bio

    if needs_photo and new_photo:
        author.photo = new_photo
        updated_fields['photo'] = new_photo

    new_birth = wd_birth or group_data.get('birth_date')
    new_death = wd_death or group_data.get('death_date')

    if needs_dates and new_birth:
        author.birth_date = new_birth
        updated_fields['birth_date'] = new_birth

    if needs_dates and new_death:
        author.death_date = new_death
        updated_fields['death_date'] = new_death

    # Save wikidata_id if found
    if wikidata_qid and not author.wikidata_id:
        author.wikidata_id = wikidata_qid
        updated_fields['wikidata_id'] = wikidata_qid

    if updated_fields:
        author.save(update_fields=list(updated_fields.keys()) + ['updated_at'])
        logger.info(f'Enriched author "{author.name}": {list(updated_fields.keys())}')

    # Auto-link authors sharing the same Wikidata QID
    if wikidata_qid and not author.author_group_id:
        _auto_link_by_wikidata(author, wikidata_qid)

    return updated_fields


def _auto_link_by_wikidata(author, qid):
    """
    If another Author has the same wikidata_id, link them in an AuthorGroup.
    The author with the most books becomes primary.
    """
    from apps.books.models import Author as AuthorModel, AuthorGroup

    existing = (
        AuthorModel.objects
        .filter(wikidata_id=qid)
        .exclude(id=author.id)
        .first()
    )
    if not existing:
        return

    # Already in the same group
    if (author.author_group_id and existing.author_group_id
            and author.author_group_id == existing.author_group_id):
        return

    # Determine which group to use (or create new)
    if existing.author_group_id:
        group = existing.author_group
    elif author.author_group_id:
        group = author.author_group
    else:
        # Pick primary by book count
        author_count = author.books.count()
        existing_count = existing.books.count()
        primary = existing if existing_count >= author_count else author
        group = AuthorGroup.objects.create(canonical_name=primary.name)
        primary.is_primary_alias = True
        primary.author_group = group
        primary.save(update_fields=['author_group', 'is_primary_alias', 'updated_at'])

    # Link the other author to the group
    if not author.author_group_id:
        author.author_group = group
        author.save(update_fields=['author_group', 'updated_at'])
    if not existing.author_group_id:
        existing.author_group = group
        existing.save(update_fields=['author_group', 'updated_at'])

    logger.info(
        f'Auto-linked authors by Wikidata {qid}: '
        f'"{author.name}" <-> "{existing.name}" (group={group.id})'
    )


# ─── Group sibling data ──────────────────────────────────────

def _get_group_sibling_data(author):
    """
    If author is in a group, return data from a sibling that has bio/photo/dates.
    This handles transliterated names (e.g. "Viktor Igo" → copy from "Victor Hugo").
    """
    if not author.author_group_id:
        return {}

    siblings = (
        author.author_group.members
        .exclude(id=author.id)
        .order_by('-is_primary_alias')
    )

    result = {}
    for sib in siblings:
        if sib.is_primary_alias or not result.get('primary_name'):
            result['primary_name'] = sib.name
        if sib.bio and not result.get('bio'):
            result['bio'] = sib.bio
        if sib.photo and not result.get('photo'):
            result['photo'] = sib.photo
        if sib.birth_date and not result.get('birth_date'):
            result['birth_date'] = sib.birth_date
        if sib.death_date and not result.get('death_date'):
            result['death_date'] = sib.death_date
        if sib.wikidata_id and not result.get('wikidata_id'):
            result['wikidata_id'] = sib.wikidata_id

    return result


# ─── Open Library ────────────────────────────────────────────

def _search_open_library(name):
    try:
        resp = requests.get(
            'https://openlibrary.org/search/authors.json',
            params={'q': name},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        docs = resp.json().get('docs', [])
        if docs:
            top = docs[0]
            return {'olid': top.get('key', ''), 'name': top.get('name', '')}
    except requests.RequestException as e:
        logger.debug(f'OL search failed for "{name}": {e}')
    return None


def _get_ol_author_detail(olid):
    try:
        resp = requests.get(
            f'https://openlibrary.org/authors/{olid}.json',
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.debug(f'OL detail failed for {olid}: {e}')
    return None


# ─── Wikipedia ───────────────────────────────────────────────

def _search_wikipedia(name):
    try:
        resp = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'list': 'search',
                'srsearch': name,
                'srlimit': 3,
                'format': 'json',
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get('query', {}).get('search', [])
        if results:
            return results[0]['title'].replace(' ', '_')
    except requests.RequestException as e:
        logger.debug(f'Wiki search failed for "{name}": {e}')
    return None


def _get_wikipedia_summary(page_title):
    try:
        encoded = quote(page_title, safe='')
        resp = requests.get(
            f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}',
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.debug(f'Wiki summary failed for "{page_title}": {e}')
    return None


def _get_wikipedia_title_from_wikidata(qid):
    try:
        resp = requests.get(
            'https://www.wikidata.org/w/api.php',
            params={
                'action': 'wbgetentities',
                'ids': qid,
                'props': 'sitelinks',
                'sitefilter': 'enwiki',
                'format': 'json',
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        entities = resp.json().get('entities', {})
        entity = entities.get(qid, {})
        title = entity.get('sitelinks', {}).get('enwiki', {}).get('title')
        if title:
            return title.replace(' ', '_')
    except requests.RequestException:
        pass
    return None


# ─── Wikidata ────────────────────────────────────────────────

def _get_wikidata_dates(qid):
    try:
        resp = requests.get(
            f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json',
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        entities = resp.json().get('entities', {})
        claims = entities.get(qid, {}).get('claims', {})
        birth = _parse_wikidata_date(claims.get('P569', []))
        death = _parse_wikidata_date(claims.get('P570', []))
        return birth, death
    except requests.RequestException as e:
        logger.debug(f'Wikidata failed for {qid}: {e}')
    return None, None


def _parse_wikidata_date(claim_list):
    if not claim_list:
        return None
    try:
        time_str = (
            claim_list[0]
            .get('mainsnak', {})
            .get('datavalue', {})
            .get('value', {})
            .get('time', '')
        )
        if not time_str:
            return None
        clean = time_str.lstrip('+')
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})', clean)
        if match:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if m == 0:
                m = 1
            if d == 0:
                d = 1
            return datetime.date(y, m, d)
    except (IndexError, KeyError, ValueError, TypeError):
        pass
    return None
