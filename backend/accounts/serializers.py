"""
Accounts serializers.

Handles user registration, profile viewing/updating, and password changes.
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


def validate_phone_number(value):
    """
    Shared phone validation used by both RegisterSerializer and UserProfileSerializer.

    Allows digits, +, -, spaces, and parentheses.
    Cleaned number (digits only) must be 7-15 characters.
    """
    if value:
        cleaned = re.sub(r'[\s\-\+\(\)]', '', value)
        if not cleaned.isdigit():
            raise serializers.ValidationError(
                "Phone number can only contain digits, +, -, spaces, and parentheses."
            )
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise serializers.ValidationError(
                "Phone number must be between 7 and 15 digits."
            )
    return value

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    - Validates password strength via Django's built-in validators.
    - Prevents role escalation: 'role' is NOT accepted from client input.
    - Uses create_user() to ensure password is hashed.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone", "password"]
        extra_kwargs = {
            "email": {"required": True},
            "full_name": {"required": True},
        }

    def validate_email(self, value):
        """Case-insensitive email uniqueness check."""
        normalized = value.lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return normalized

    def validate_phone(self, value):
        """Delegate to shared validator."""
        return validate_phone_number(value)

    def create(self, validated_data):
        """
        Create user via manager's create_user().
        Ensures password is hashed and role defaults to 'user'.
        """
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
        )

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating the authenticated user's profile.

    email, role, created_at are read-only:
    - email: changing email needs a separate verified flow.
    - role: prevents privilege escalation.
    - created_at: system-managed.
    """

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "role", "created_at"]
        read_only_fields = ["id", "email", "role", "created_at"]

    def validate_phone(self, value):
        """Same phone validation as registration — shared validator."""
        return validate_phone_number(value)

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing the authenticated user's password.

    Requires old password for verification before setting a new one.
    """

    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from current password."}
            )
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Lowercases email before authentication so login is case-insensitive.
    Adds role and email to the JWT payload so the frontend can read them
    without a separate API call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to JWT payload
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].lower()
        return super().validate(attrs)
