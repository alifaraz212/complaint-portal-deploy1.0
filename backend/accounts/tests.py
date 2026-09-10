import json
import base64
import pytest
from rest_framework import status
from accounts.models import User

@pytest.mark.django_db
class TestUserRegistration:

    def test_valid_registration(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone': '+92 300 1234567',
            'password': 'StrongPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@example.com').exists()
        user = User.objects.get(email='newuser@example.com')
        assert user.role == 'user'

    def test_duplicate_email_rejected(self, api_client, test_user):
        response = api_client.post('/api/auth/register/', {
            'email': 'user@example.com',  # already exists from fixture
            'full_name': 'Another User',
            'password': 'StrongPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'email': 'weakpass@example.com',
            'full_name': 'Weak User',
            'password': '123456',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_rejected(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'email': 'badphone@example.com',
            'full_name': 'Bad Phone',
            'password': 'StrongPassword123!',
            'phone': 'not-a-phone',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_register_as_admin(self, api_client):
        response = api_client.post('/api/auth/register/', {
            'email': 'hacker@example.com',
            'full_name': 'Hacker',
            'password': 'StrongPassword123!',
            'role': 'admin',  # try to claim admin role
        }, format='json')

        # Even if request succeeds, role must be 'user'
        user = User.objects.get(email='hacker@example.com')
        assert user.role == 'user'

@pytest.mark.django_db
class TestUserLogin:

    def test_valid_login_returns_tokens(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {
            'email': 'user@example.com',
            'password': 'TestPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_jwt_contains_role_and_email(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {
            'email': 'user@example.com',
            'password': 'TestPassword123!',
        }, format='json')

        # Decode JWT payload (middle part)
        token = response.data['access']
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)  # fix padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))

        assert decoded['email'] == 'user@example.com'
        assert decoded['role'] == 'user'

    def test_wrong_password_rejected(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {
            'email': 'user@example.com',
            'password': 'WrongPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_rejected(self, api_client):
        response = api_client.post('/api/auth/login/', {
            'email': 'ghost@example.com',
            'password': 'AnyPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
