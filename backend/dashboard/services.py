"""
Dashboard business logic service layer.

Centralizes all statistics computation so it can be called from
views, serializers, or management commands.
"""

from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

from complaints.models import Complaint, Category, ActivityLog

def get_dashboard_stats():
    """
    Compute all dashboard statistics via database aggregation.

    Returns a dict with:
    - total_complaints
    - by_status
    - by_priority
    - by_category
    - average_resolution_time_hours
    - this_month_count
    - last_month_count
    """

    # 1. Total complaints (excluding archived)
    total = Complaint.active.count()

    # 2. By status
    by_status = dict(
        Complaint.active
        .values('status')
        .annotate(count=Count('id'))
        .values_list('status', 'count')
    )

    # 3. By priority
    by_priority = dict(
        Complaint.active
        .values('priority')
        .annotate(count=Count('id'))
        .filter(priority__isnull=False)
        .values_list('priority', 'count')
    )
    by_priority['unassigned'] = Complaint.active.filter(priority__isnull=True).count()

    # 4. By category
    by_category = dict(
        Category.objects
        .annotate(count=Count('complaints'))
        .values_list('name', 'count')
    )

    # 5. Average resolution time (only resolved complaints)
    resolved_stats = Complaint.active.filter(
        status=Complaint.Status.RESOLVED,
        resolved_at__isnull=False
    ).aggregate(
        avg_duration=Avg(F('resolved_at') - F('created_at'))
    )
    # Convert timedelta to hours
    avg_duration = resolved_stats.get('avg_duration')
    avg_hours = avg_duration.total_seconds() / 3600 if avg_duration else 0

    # 6. This month vs last month
    today = timezone.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    this_month = Complaint.active.filter(
        created_at__gte=month_start
    ).count()

    last_month = Complaint.active.filter(
        created_at__gte=last_month_start,
        created_at__lt=month_start
    ).count()

    return {
        'total_complaints': total,
        'by_status': by_status,
        'by_priority': by_priority,
        'by_category': by_category,
        'average_resolution_time_hours': avg_hours,
        'this_month_count': this_month,
        'last_month_count': last_month,
    }

def get_recent_activity():
    """
    Get recent complaints and status changes.

    Returns a dict with:
    - recent_complaints: last 10 submitted
    - recent_status_changes: last 10 status_changed logs
    """
    from complaints.serializers import ComplaintListSerializer, ActivityLogSerializer

    # Last 10 complaints
    complaints = Complaint.active.order_by('-created_at')[:10]
    recent_complaints = ComplaintListSerializer(complaints, many=True).data

    # Last 10 status changes
    changes = ActivityLog.objects.filter(
        action='status_changed'
    ).select_related('performed_by', 'complaint').order_by('-timestamp')[:10]
    recent_status_changes = ActivityLogSerializer(changes, many=True).data

    return {
        'recent_complaints': recent_complaints,
        'recent_status_changes': recent_status_changes,
    }
