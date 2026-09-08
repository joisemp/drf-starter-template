from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import (
    ChangePasswordView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)

app_name = "users"

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),

    # JWT token endpoints
    path("login/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),

    # Profile
    path("me/", MeView.as_view(), name="me"),

    # Auth actions
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),

    # Password reset
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
