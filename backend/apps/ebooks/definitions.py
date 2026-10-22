"""
Suggests what a word means *in the sentence it was read in*, via Gemini.
The user always sees and can edit the suggestion before saving the word.
"""
import hashlib
import json

import requests
from decouple import config
from django.core.cache import cache

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
TIMEOUT = 25
CACHE_SECONDS = 30 * 24 * 3600

PROMPT = """You help a reader build a personal vocabulary.
Word: "{word}"
Sentence it appeared in: "{context}"

Explain what the word means in THIS sentence, in the same language as the sentence
(if the sentence is in Serbian, answer in Serbian using the same script, Cyrillic or Latin).
Be concise: one or two short sentences, no preamble. If it is archaic, dialectal or a
biblical/literary term, say so briefly.
Reply as JSON: {{"definition": "..."}}"""


class DefinitionUnavailable(Exception):
    pass


def suggest_definition(word, context):
    api_key = config('GEMINI_API_KEY', default='')
    if not api_key:
        raise DefinitionUnavailable('Definitions are not configured (GEMINI_API_KEY).')

    word = word.strip()[:100]
    context = (context or word).strip()[:1000]
    key = 'ebook-define:' + hashlib.md5(f'{word}\n{context}'.encode()).hexdigest()
    cached = cache.get(key)
    if cached:
        return cached

    model = config('GEMINI_MODEL', default='gemini-3-flash-preview')
    try:
        response = requests.post(
            GEMINI_URL.format(model=model),
            params={'key': api_key},
            json={
                'contents': [{'parts': [{'text': PROMPT.format(word=word, context=context)}]}],
                'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.2},
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        text = response.json()['candidates'][0]['content']['parts'][0]['text']
        definition = str(json.loads(text).get('definition', '')).strip()
    except (requests.RequestException, KeyError, IndexError, ValueError, TypeError) as exc:
        raise DefinitionUnavailable('Could not get a definition right now.') from exc

    if not definition:
        raise DefinitionUnavailable('No definition returned.')
    cache.set(key, definition, CACHE_SECONDS)
    return definition
