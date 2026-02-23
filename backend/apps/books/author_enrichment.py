"""
Author enrichment utility — fetches bio, photo, and dates from
Open Library, Wikipedia, and Wikidata.

Can be called directly for a single author or in bulk via management command.
"""

import re
import logging
import datetime
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

HEADERS = {'User-Agent': 'ReadingOS/1.0 (book-tracker)'}
REQUEST_TIMEOUT = 15


def enrich_author(author, force=False):
    """
    Enrich a single Author instance with external data.
    Returns dict of fields that were updated, or empty dict if nothing changed.

    Pipeline:
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

    # Step 1: Open Library
    wikidata_qid = None
    ol_bio = ''
    ol_photo = ''

    ol_data = _search_open_library(author.name)
    if ol_data:
        olid = ol_data.get('olid')
        if olid:
            ol_detail = _get_ol_author_detail(olid)
            if ol_detail:
                wikidata_qid = (ol_detail.get('remote_ids') or {}).get('wikidata')
                bio_raw = ol_detail.get('bio')
                if isinstance(bio_raw, dict):
                    ol_bio = bio_raw.get('value', '')
                elif isinstance(bio_raw, str):
                    ol_bio = bio_raw
                photos = ol_detail.get('photos', [])
                valid_photos = [p for p in photos if isinstance(p, int) and p > 0]
                if valid_photos:
                    ol_photo = f'https://covers.openlibrary.org/a/id/{valid_photos[0]}-M.jpg'
                elif olid:
                    ol_photo = f'https://covers.openlibrary.org/a/olid/{olid}-M.jpg'

    # Step 2: Wikipedia
    wiki_bio = ''
    wiki_photo = ''
    wiki_page_title = None

    if wikidata_qid:
        wiki_page_title = _get_wikipedia_title_from_wikidata(wikidata_qid)
    if not wiki_page_title:
        wiki_page_title = _search_wikipedia(author.name)

    if wiki_page_title:
        wiki_data = _get_wikipedia_summary(wiki_page_title)
        if wiki_data:
            wiki_bio = wiki_data.get('extract', '')
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

    # Merge (Wikipedia preferred, OL as fallback)
    new_bio = wiki_bio or ol_bio
    new_photo = wiki_photo or ol_photo

    # Apply updates
    updated_fields = {}

    if needs_bio and new_bio:
        author.bio = new_bio
        updated_fields['bio'] = new_bio

    if needs_photo and new_photo:
        author.photo = new_photo
        updated_fields['photo'] = new_photo

    if needs_dates and wd_birth:
        author.birth_date = wd_birth
        updated_fields['birth_date'] = wd_birth

    if needs_dates and wd_death:
        author.death_date = wd_death
        updated_fields['death_date'] = wd_death

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
