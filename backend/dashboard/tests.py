import pytest
from rest_framework import status
from complaints.models import Complaint

@pytest.mark.django_db
class TestDashboardAccess:

    def test_admin_can_access_stats(self, admin_client):
        response = admin_client.get('/api/dashboard/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_access_stats(self, authenticated_client):
        response = authenticated_client.get('/api/dashboard/stats/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_stats(self, api_client):
        response = api_client.get('/api/dashboard/stats/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_can_access_recent(self, admin_client):
        response = admin_client.get('/api/dashboard/recent/')
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_access_recent(self, authenticated_client):
        response = authenticated_client.get('/api/dashboard/recent/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestDashboardStats:

    def test_stats_response_shape(self, admin_client):
        response = admin_client.get('/api/dashboard/stats/')

        assert 'total_complaints' in response.data
        assert 'by_status' in response.data
        assert 'by_priority' in response.data
        assert 'by_category' in response.data
        assert 'average_resolution_time_hours' in response.data
        assert 'this_month_count' in response.data
        assert 'last_month_count' in response.data

    def test_stats_correct_total(self, admin_client, test_user, test_category):
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='C1', description='', status='open'
        )
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='C2', description='', status='open'
        )
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='C3', description='', status='in_progress'
        )

        response = admin_client.get('/api/dashboard/stats/')

        assert response.data['total_complaints'] == 3

    def test_stats_by_status_counts(self, admin_client, test_user, test_category):
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='Open 1', description='', status='open'
        )
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='Open 2', description='', status='open'
        )
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='In Progress', description='', status='in_progress'
        )
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='Resolved', description='', status='resolved'
        )

        response = admin_client.get('/api/dashboard/stats/')

        assert response.data['by_status']['open'] == 2
        assert response.data['by_status']['in_progress'] == 1
        assert response.data['by_status']['resolved'] == 1
        assert response.data['by_status']['closed'] == 0  # zero, not missing

    def test_stats_archived_excluded(self, admin_client, test_user, test_category):
        Complaint.objects.create(
            user=test_user, category=test_category,
            subject='Active', description='', status='open'
        )
        archived = Complaint.objects.create(
            user=test_user, category=test_category,
            subject='Archived', description='', status='open'
        )
        archived.is_archived = True
        archived.save()

        response = admin_client.get('/api/dashboard/stats/')

        assert response.data['total_complaints'] == 1  # archived excluded

@pytest.mark.django_db
class TestRecentActivity:

    def test_recent_complaints_in_response(self, admin_client, test_complaint):
        response = admin_client.get('/api/dashboard/recent/')

        assert 'recent_complaints' in response.data
        assert 'recent_status_changes' in response.data

    def test_recent_complaints_max_10(self, admin_client, test_user, test_category):
        for i in range(15):
            Complaint.objects.create(
                user=test_user, category=test_category,
                subject=f'Complaint {i}', description=''
            )

        response = admin_client.get('/api/dashboard/recent/')

        assert len(response.data['recent_complaints']) <= 10
