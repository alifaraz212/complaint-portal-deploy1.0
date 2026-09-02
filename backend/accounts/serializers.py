"""
Accounts serializers.

Handles user registration, profile viewing/updating, and password changes.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

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
