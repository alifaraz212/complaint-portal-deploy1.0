from django.urls import path
from .views import StatsAPIView, RecentActivityView

urlpatterns = [
    path('stats/', StatsAPIView.as_view(), name='dashboard-stats'),
    path('recent/', RecentActivityView.as_view(), name='dashboard-recent'),
]
