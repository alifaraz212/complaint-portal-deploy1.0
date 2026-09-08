from rest_framework import serializers


class StatisticsSerializer(serializers.Serializer):
    """
    Serializes dashboard statistics.
    Logic computed in services.py, serializer just validates format.
    """

    total_complaints = serializers.IntegerField()

    # DictField with IntegerField child — all values must be integers
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_priority = serializers.DictField(child=serializers.IntegerField())
    by_category = serializers.DictField(child=serializers.IntegerField())

    # Float to preserve precision (e.g. 0.0833 hours = 5 minutes)
    average_resolution_time_hours = serializers.FloatField()

    this_month_count = serializers.IntegerField()
    last_month_count = serializers.IntegerField()


class RecentActivitySerializer(serializers.Serializer):
    """
    Serializes recent activity.
    Logic computed in services.py, serializer just validates format.
    """

    # ListField with DictField child — list of complaint/activity objects
    recent_complaints = serializers.ListField(child=serializers.DictField())
    recent_status_changes = serializers.ListField(child=serializers.DictField())
