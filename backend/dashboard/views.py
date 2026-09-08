from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from accounts.permissions import IsAdmin
from .services import get_dashboard_stats, get_recent_activity
from .serializers import StatisticsSerializer, RecentActivitySerializer

class StatsAPIView(generics.GenericAPIView):
    """
    GET /api/dashboard/stats/

    Returns aggregated statistics about all complaints.
    Admin only.
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = StatisticsSerializer

    def get(self, request):
        """Compute and return statistics via service layer."""
        stats = get_dashboard_stats()
        serializer = StatisticsSerializer(stats)
        return DRFResponse(serializer.data, status=status.HTTP_200_OK)

class RecentActivityView(generics.GenericAPIView):
    """
    GET /api/dashboard/recent/

    Returns recent complaints and status changes.
    Admin only.
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RecentActivitySerializer

    def get(self, request):
        """Return recent activity via service layer."""
        activity = get_recent_activity()
        serializer = RecentActivitySerializer(activity)
        return DRFResponse(serializer.data, status=status.HTTP_200_OK)
