import pytest
from unittest.mock import patch

HEALTH_URL = "/api/health/"


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_returns_200(self, api_client):
        """Healthcheck should return 200 when DB and Redis are reachable."""
        with patch("apps.healthcheck.views.HealthCheckView._check_redis", return_value="ok"):
            response = api_client.get(HEALTH_URL)
        assert response.status_code == 200
        assert response.data["status"] == "ok"
        assert response.data["db"] == "ok"
        assert response.data["redis"] == "ok"

    def test_health_returns_503_when_redis_down(self, api_client):
        """Healthcheck should return 503 when Redis is unreachable."""
        with patch("apps.healthcheck.views.HealthCheckView._check_redis", return_value="error"):
            response = api_client.get(HEALTH_URL)
        assert response.status_code == 503
        assert response.data["status"] == "degraded"

    def test_health_accessible_without_auth(self, api_client):
        """Healthcheck must be publicly accessible (no auth required)."""
        with patch("apps.healthcheck.views.HealthCheckView._check_redis", return_value="ok"):
            response = api_client.get(HEALTH_URL)
        assert response.status_code != 401
