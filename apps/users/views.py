import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthRateThrottle(AnonRateThrottle):
    rate = "10/min"
    scope = "auth"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@extend_schema(tags=["Auth"])
class RegisterView(generics.CreateAPIView):
    """Register a new user with email and password."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New user registered: %s", user.email)
        return Response(
            {"detail": "Account created successfully."},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@extend_schema(tags=["Auth"])
class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Change Password
# ---------------------------------------------------------------------------
@extend_schema(tags=["Auth"])
class ChangePasswordView(generics.GenericAPIView):
    """Change password for the authenticated user."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        logger.info("Password changed for user: %s", request.user.email)
        return Response({"detail": "Password updated successfully."})


# ---------------------------------------------------------------------------
# Logout (blacklist refresh token)
# ---------------------------------------------------------------------------
@extend_schema(tags=["Auth"])
class LogoutView(generics.GenericAPIView):
    """Blacklist the refresh token to log out."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: %s", request.user.email)
            return Response({"detail": "Successfully logged out."})
        except Exception:
            return Response(
                {"detail": "Invalid or already blacklisted token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------
@extend_schema(tags=["Auth"])
class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request a password reset email.

    In development, the email is printed to the terminal.
    Always returns 200 to prevent email enumeration.
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{request.scheme}://{request.get_host()}/api/auth/password/reset/confirm/?uid={uid}&token={token}"

            subject = "Password Reset Request"
            message = (
                f"Hi {user.full_name},\n\n"
                f"You requested a password reset. Click the link below to set a new password:\n\n"
                f"{reset_url}\n\n"
                f"This link expires in 1 hour.\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"— The Inveno Team"
            )
            send_mail(subject, message, None, [email], fail_silently=False)
            logger.info("Password reset email sent to: %s", email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists
            logger.debug("Password reset requested for non-existent email: %s", email)

        return Response(
            {"detail": "If an account with that email exists, a reset link has been sent."}
        )


@extend_schema(tags=["Auth"])
class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset with uid + token from the email link."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        logger.info("Password reset completed for user: %s", user.email)
        return Response({"detail": "Password has been reset successfully."})
