from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import IsAdminUser

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/", include("apps.healthcheck.urls")),
    path("api/auth/", include("apps.users.urls")),

    # API Documentation — superuser only (log in at /admin/ first)
    path("api/schema/", SpectacularAPIView.as_view(
        permission_classes=[IsAdminUser]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(
        url_name="schema", permission_classes=[IsAdminUser]), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(
        url_name="schema", permission_classes=[IsAdminUser]), name="redoc"),
]
