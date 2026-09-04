"""
Complaint serializers.

Separate serializers for different operations:
- CategorySerializer: CRUD for categories (admin)
- ComplaintAttachmentSerializer: Upload and list attachments
- ComplaintCreateSerializer: User submits a new complaint
- ComplaintListSerializer: Listing complaints (lightweight)
- ComplaintDetailSerializer: Full complaint with responses and activity
- ComplaintUpdateSerializer: Admin updates status/priority
- ResponseSerializer: Add/view responses in conversation thread
- ActivityLogSerializer: View activity log entries
"""

from rest_framework import serializers

from .models import ActivityLog, Category, Complaint, Response, ComplaintAttachment
from .services import (
    add_response,
    create_complaint,
    update_complaint_priority,
    update_complaint_status,
    validate_status_transition,
)


# ─────────────────────────────────────────────────────────────────────
# Attachment
# ─────────────────────────────────────────────────────────────────────

class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading complaint attachments (images).
    
    File is uploaded and stored on disk. Only file path stored in DB.
    """

    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ComplaintAttachment
        fields = ["id", "file", "file_url", "uploaded_at"]
        read_only_fields = ["id", "file_url", "uploaded_at"]

    def get_file_url(self, obj):
        """Return the full URL to the uploaded file."""
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


# ─────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    """
    Full category serializer for admin CRUD.

    All fields are editable by admin.
    For listing (authenticated users), is_active is read-only
    but that's handled at the view level (filtering active only).
    """

    class Meta:
        model = Category
        fields = ["id", "name", "description", "is_active"]

    def validate_name(self, value):
        """Case-insensitive uniqueness for category names."""
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )
        return value


# ─────────────────────────────────────────────────────────────────────
# Complaint — Create
# ─────────────────────────────────────────────────────────────────────

class ComplaintCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for submitting a new complaint.

    User provides: subject, description, category.
    System auto-sets: complaint_number, status, user, timestamps.
    Attachments are handled separately via ComplaintAttachment model.

    Security:
    - 'user' is set from request.user in the view (not from input).
    - 'status', 'priority', 'admin_notes' are not accepted.
    - 'complaint_number' is auto-generated.
    """

    class Meta:
        model = Complaint
        fields = ["subject", "description", "category"]

    def validate_category(self, value):
        """Only active categories can be used for new complaints."""
        if not value.is_active:
            raise serializers.ValidationError(
                "This category is not currently active."
            )
        return value

    def create(self, validated_data):
        """
        Delegate to the service layer for complaint creation.

        The service handles:
        - Saving the complaint with auto-generated complaint_number
        - Creating the initial ActivityLog entry
        - Attachments are uploaded separately after complaint creation
        """
        user = self.context["request"].user
        return create_complaint(
            user=user,
            category=validated_data["category"],
            subject=validated_data["subject"],
            description=validated_data["description"],
        )


# ─────────────────────────────────────────────────────────────────────
# Complaint — List (lightweight)
# ─────────────────────────────────────────────────────────────────────

class ComplaintListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for complaint list views.

    Includes category name and user email for display.
    Does NOT include responses or activity logs (too heavy for lists).
    """

    category_name = serializers.CharField(source="category.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "subject",
            "status",
            "priority",
            "category",
            "category_name",
            "user_email",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────
# Response
# ─────────────────────────────────────────────────────────────────────

class ResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for complaint responses (conversation thread).

    'author' is set from request.user in the view.
    'author_email' and 'author_role' are read-only display fields.
    """

    author_email = serializers.EmailField(source="author.email", read_only=True)
    author_role = serializers.CharField(source="author.role", read_only=True)

    class Meta:
        model = Response
        fields = [
            "id",
            "message",
            "author",
            "author_email",
            "author_role",
            "created_at",
        ]
        read_only_fields = ["id", "author", "author_email", "author_role", "created_at"]

    def create(self, validated_data):
        """Delegate to service layer for response creation + activity logging."""
        complaint = self.context["complaint"]
        author = self.context["request"].user
        return add_response(
            complaint=complaint,
            author=author,
            message=validated_data["message"],
        )


# ─────────────────────────────────────────────────────────────────────
# ActivityLog
# ─────────────────────────────────────────────────────────────────────

class ActivityLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for activity log entries."""

    performed_by_email = serializers.EmailField(
        source="performed_by.email", read_only=True
    )

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "action",
            "old_value",
            "new_value",
            "performed_by",
            "performed_by_email",
            "timestamp",
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────
# Complaint — Detail (full, with nested responses + activity)
# ─────────────────────────────────────────────────────────────────────

class ComplaintDetailSerializer(serializers.ModelSerializer):
    """
    Full complaint serializer including nested responses and activity logs.

    Used for the detail view. Includes all fields plus:
    - category_name for display
    - user_email for display
    - responses: full conversation thread
    - activity_logs: full audit trail (admin only — handled in view)
    - attachments: list of file attachments
    """

    category_name = serializers.CharField(source="category.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)
    responses = ResponseSerializer(many=True, read_only=True)
    activity_logs = ActivityLogSerializer(many=True, read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "subject",
            "description",
            "status",
            "priority",
            "admin_notes",
            "category",
            "category_name",
            "user",
            "user_email",
            "created_at",
            "updated_at",
            "resolved_at",
            "responses",
            "activity_logs",
            "attachments",
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────
# Complaint — Update (admin operations)
# ─────────────────────────────────────────────────────────────────────

class ComplaintUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a complaint's status, priority, and admin_notes.

    This is a plain Serializer (not ModelSerializer) because:
    - We need custom validation for status transitions.
    - We delegate to the service layer for actual updates.
    - We don't want the client to set arbitrary fields.

    Admin can update:
    - status: Must follow the workflow rules.
    - priority: low/medium/high/urgent.
    - admin_notes: Internal notes (not visible to user).
    """

    status = serializers.ChoiceField(
        choices=Complaint.Status.choices,
        required=False,
    )
    priority = serializers.ChoiceField(
        choices=Complaint.Priority.choices,
        required=False,
    )
    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_status(self, value):
        """Validate status transition against workflow rules."""
        complaint = self.context["complaint"]
        is_valid, error = validate_status_transition(complaint.status, value)
        if not is_valid:
            raise serializers.ValidationError(error)
        return value

    def update(self, complaint, validated_data):
        """
        Apply updates through the service layer.

        Each update type (status, priority, admin_notes) is handled
        separately so activity logging is granular.
        """
        user = self.context["request"].user

        if "status" in validated_data:
            complaint = update_complaint_status(
                complaint=complaint,
                new_status=validated_data["status"],
                performed_by=user,
            )

        if "priority" in validated_data:
            complaint = update_complaint_priority(
                complaint=complaint,
                new_priority=validated_data["priority"],
                performed_by=user,
            )

        if "admin_notes" in validated_data:
            complaint.admin_notes = validated_data["admin_notes"]
            complaint.save(update_fields=["admin_notes", "updated_at"])

        return complaint
