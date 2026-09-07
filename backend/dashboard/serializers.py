from rest_framework import serializers

class StatisticsSerializer(serializers.Serializer):
    """
    Serializes dashboard statistics.
    Logic computed in services.py, serializer just validates format.
    """

    total_complaints = serializers.IntegerField()
    by_status = serializers.DictField()
    by_priority = serializers.DictField()
    by_category = serializers.DictField()
    average_resolution_time_hours = serializers.FloatField()
    this_month_count = serializers.IntegerField()
    last_month_count = serializers.IntegerField()

class RecentActivitySerializer(serializers.Serializer):
    """
    Serializes recent activity.
    Logic computed in services.py, serializer just validates format.
    """

    recent_complaints = serializers.ListField()
    recent_status_changes = serializers.ListField()
