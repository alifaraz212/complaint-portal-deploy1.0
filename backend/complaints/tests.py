import pytest
from rest_framework import status
from complaints.models import Complaint, ActivityLog

@pytest.mark.django_db
class TestComplaintCreation:

    def test_user_can_create_complaint(self, authenticated_client, test_category, test_user):
        response = authenticated_client.post('/api/complaints/complaints/', {
            'category': test_category.id,
            'subject': 'Internet problem',
            'description': 'My internet is unstable.',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        complaint = Complaint.objects.get(subject='Internet problem')
        assert complaint.user == test_user
        assert complaint.status == Complaint.Status.OPEN
        assert complaint.complaint_number.startswith('CMP-')

    def test_complaint_creation_logs_activity(self, authenticated_client, test_category):
        response = authenticated_client.post('/api/complaints/complaints/', {
            'category': test_category.id,
            'subject': 'Activity log test',
            'description': 'Testing activity logging.',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        complaint = Complaint.objects.get(subject='Activity log test')
        assert complaint.activity_logs.filter(action='created').exists()

    def test_unauthenticated_cannot_create(self, api_client, test_category):
        response = api_client.post('/api/complaints/complaints/', {
            'category': test_category.id,
            'subject': 'Unauthorized',
            'description': 'Should fail.',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestComplaintWorkflow:

    def test_valid_transition_open_to_in_progress(self, admin_client, test_complaint):
        response = admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'in_progress'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        test_complaint.refresh_from_db()
        assert test_complaint.status == 'in_progress'

    def test_valid_full_workflow(self, admin_client, test_complaint):
        # open → in_progress
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'in_progress'}, format='json'
        )
        # in_progress → resolved
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'resolved'}, format='json'
        )
        # resolved → closed
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'closed'}, format='json'
        )

        test_complaint.refresh_from_db()
        assert test_complaint.status == 'closed'

    def test_resolved_at_set_when_resolved(self, admin_client, test_complaint):
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'in_progress'}, format='json'
        )
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'resolved'}, format='json'
        )

        test_complaint.refresh_from_db()
        assert test_complaint.resolved_at is not None

    def test_invalid_transition_open_to_resolved(self, admin_client, test_complaint):
        response = admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'resolved'}, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        test_complaint.refresh_from_db()
        assert test_complaint.status == 'open'  # unchanged

    def test_invalid_transition_open_to_closed(self, admin_client, test_complaint):
        response = admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'closed'}, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        test_complaint.refresh_from_db()
        assert test_complaint.status == 'open'  # unchanged

    def test_invalid_transition_closed_is_terminal(self, admin_client, test_complaint):
        # Move to closed first
        test_complaint.status = 'closed'
        test_complaint.save()

        response = admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'open'}, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        test_complaint.refresh_from_db()
        assert test_complaint.status == 'closed'  # unchanged

    def test_status_change_logs_activity(self, admin_client, test_complaint):
        admin_client.patch(
            f'/api/complaints/complaints/{test_complaint.id}/update/',
            {'status': 'in_progress'}, format='json'
        )

        log = ActivityLog.objects.filter(
            complaint=test_complaint,
            action='status_changed'
        ).first()

        assert log is not None
        assert log.old_value == 'open'
        assert log.new_value == 'in_progress'

@pytest.mark.django_db
class TestComplaintPermissions:

    def test_user_can_see_own_complaint(self, authenticated_client, test_complaint):
        response = authenticated_client.get(
            f'/api/complaints/complaints/{test_complaint.id}/'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_see_other_users_complaint(self, api_client, test_complaint, db):
        from accounts.models import User
        other_user = User.objects.create_user(
            email='other@example.com',
            full_name='Other User',
            password='OtherPassword123!',
            role='user',
        )
        api_client.force_authenticate(user=other_user)

        response = api_client.get(
            f'/api/complaints/complaints/{test_complaint.id}/'
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_admin_can_see_any_complaint(self, admin_client, test_complaint):
        response = admin_client.get(
            f'/api/complaints/complaints/{test_complaint.id}/'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_see_complaint(self, api_client, test_complaint):
        response = api_client.get(
            f'/api/complaints/complaints/{test_complaint.id}/'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
