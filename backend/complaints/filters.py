"""
Complaint filters using django-filter.

Provides filtering by status, priority, category, date range,
and search by subject/description.
"""

import django_filters

from .models import Complaint


class ComplaintFilter(django_filters.FilterSet):
    """
    Filter set for complaint list views.

    Supports:
    - status: exact match (e.g., ?status=open)
    - priority: exact match (e.g., ?priority=high)
    - category: exact match by ID (e.g., ?category=3)
    - search: case-insensitive search in subject and description
    - date_from: complaints created on or after this date
    - date_to: complaints created on or before this date
    """

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search in subject and description",
    )
    date_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Created from (YYYY-MM-DD)",
    )
    date_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Created to (YYYY-MM-DD)",
    )

    class Meta:
        model = Complaint
        fields = ["status", "priority", "category"]

    def filter_search(self, queryset, name, value):
        """
        Search across subject and description (case-insensitive).

        Uses icontains for PostgreSQL — performs well for moderate data
        volumes. For large-scale search, consider PostgreSQL full-text
        search or a dedicated search engine.
        """
        from django.db.models import Q

        return queryset.filter(
            Q(subject__icontains=value) | Q(description__icontains=value)
        )
