import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """A basic active user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def auth_client(api_client, test_user):
    """DRF test client authenticated as test_user via JWT."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def superuser(db):
    """A superuser for admin-related tests."""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!",
    )
