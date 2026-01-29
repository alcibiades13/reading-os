"""
Custom filters for book search with accent-insensitive support.
"""

from rest_framework import filters
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models.functions import Lower
from django.contrib.postgres.lookups import Unaccent


class UnaccentSearchFilter(filters.SearchFilter):
    """
    Search filter that ignores accents (diacritics).

    This allows searching for "cevapi" and matching "ćevapi",
    or "Emili Bronte" matching "Emily Brontë".

    Uses PostgreSQL's unaccent extension.
    """

    def get_search_terms(self, request):
        """Get search terms from request."""
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # Remove null bytes
        params = params.replace(',', ' ')  # Treat commas as spaces
        return params.split()

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        # Build Q objects for each search term
        conditions = Q()

        for search_term in search_terms:
            term_conditions = Q()

            for search_field in search_fields:
                # Remove the ^ or @ prefix if present
                field_name = search_field.lstrip('^@=')

                # Use unaccent for case and accent insensitive search
                # We need to use raw SQL because Django's ORM doesn't fully support
                # unaccent with icontains in a clean way
                term_conditions |= Q(**{
                    f'{field_name}__unaccent__icontains': search_term
                })

            conditions &= term_conditions

        return queryset.filter(conditions).distinct()
