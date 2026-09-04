"""
Accounts views.

Handles user registration, profile management, and password changes.
JWT login/refresh is handled by simplejwt's built-in views (in urls.py).
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Public endpoint. Creates a new user account.
    Returns the created user's data (without password).
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "message": "Registration successful.",
            },
            status=status.HTTP_201_CREATED,
        )

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/ — View current user's profile.
    PUT  /api/auth/profile/ — Update current user's profile.

    Always operates on the requesting user's own profile.
    No ID in the URL — prevents IDOR attacks.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.GenericAPIView):
    """
    POST /api/auth/change-password/

    Requires old_password for verification and new_password.
    Uses set_password() to ensure proper hashing.
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
