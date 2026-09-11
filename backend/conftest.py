import pytest
from rest_framework.test import APIClient
from accounts.models import User
from complaints.models import Category, Complaint

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="user@example.com",
        full_name="Test User",
        password="TestPassword123!",
        role="user",
    )

@pytest.fixture
def test_admin(db):
    return User.objects.create_user(
        email="admin@example.com",
        full_name="Test Admin",
        password="AdminPassword123!",
        role="admin",
    )

@pytest.fixture
def test_category(db):
    return Category.objects.create(
        name="Test Category",
        description="Category used for automated tests.",
    )

@pytest.fixture
def test_complaint(db, test_user, test_category):
    return Complaint.objects.create(
        user=test_user,
        category=test_category,
        subject="Test complaint",
        description="Complaint created for automated tests.",
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def admin_client(api_client, test_admin):
    api_client.force_authenticate(user=test_admin)
    return api_client
