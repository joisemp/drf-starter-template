import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
TOKEN_URL = "/api/auth/token/"
TOKEN_REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/auth/me/"
LOGOUT_URL = "/api/auth/logout/"
CHANGE_PASSWORD_URL = "/api/auth/password/change/"
PASSWORD_RESET_URL = "/api/auth/password/reset/"


@pytest.mark.django_db
class TestRegistration:
    def test_register_success(self, api_client):
        payload = {
            "email": "new@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 201
        assert User.objects.filter(email="new@example.com").exists()

    def test_register_password_mismatch(self, api_client):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password2": "WrongPass123!",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 400
        assert "password2" in response.data

    def test_register_duplicate_email(self, api_client, test_user):
        payload = {
            "email": test_user.email,
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, test_user):
        response = api_client.post(TOKEN_URL, {"email": test_user.email, "password": "StrongPass123!"})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, api_client, test_user):
        response = api_client.post(TOKEN_URL, {"email": test_user.email, "password": "wrong"})
        assert response.status_code == 401

    def test_login_nonexistent_email(self, api_client):
        response = api_client.post(TOKEN_URL, {"email": "nobody@example.com", "password": "pass"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_success(self, api_client, test_user):
        login = api_client.post(TOKEN_URL, {"email": test_user.email, "password": "StrongPass123!"})
        refresh = login.data["refresh"]
        response = api_client.post(TOKEN_REFRESH_URL, {"refresh": refresh})
        assert response.status_code == 200
        assert "access" in response.data


@pytest.mark.django_db
class TestProfile:
    def test_get_me_authenticated(self, auth_client, test_user):
        response = auth_client.get(ME_URL)
        assert response.status_code == 200
        assert response.data["email"] == test_user.email

    def test_get_me_unauthenticated(self, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == 401

    def test_update_profile(self, auth_client):
        response = auth_client.patch(ME_URL, {"first_name": "Updated"})
        assert response.status_code == 200
        assert response.data["first_name"] == "Updated"


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh(self, api_client, test_user):
        login = api_client.post(TOKEN_URL, {"email": test_user.email, "password": "StrongPass123!"})
        refresh = login.data["refresh"]
        access = login.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = api_client.post(LOGOUT_URL, {"refresh": refresh})
        assert logout_response.status_code == 200

        # Blacklisted token should not work for refresh
        refresh_response = api_client.post(TOKEN_REFRESH_URL, {"refresh": refresh})
        assert refresh_response.status_code == 401


@pytest.mark.django_db
class TestPasswordReset:
    def test_reset_request_existing_email(self, api_client, test_user):
        # Should always return 200 (anti-enumeration)
        response = api_client.post(PASSWORD_RESET_URL, {"email": test_user.email})
        assert response.status_code == 200

    def test_reset_request_nonexistent_email(self, api_client):
        # Should also return 200
        response = api_client.post(PASSWORD_RESET_URL, {"email": "ghost@example.com"})
        assert response.status_code == 200
