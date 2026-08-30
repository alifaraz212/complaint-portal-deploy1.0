from django.db import models, connection
from django.conf import settings


# =============================================================================
# Category Model
# Represents the type/category of a complaint (e.g. Billing, Technical)
# =============================================================================
class Category(models.Model):

    # Name of the category, must be unique across all categories
    name = models.CharField(max_length=100, unique=True)

    # Optional description of what this category covers
    description = models.TextField(blank=True)

    # Admin can deactivate a category without deleting it
    # Deactivated categories won't appear in the complaint submission form
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        # Fixes Django's wrong auto-plural "Categorys" → "Categories"
        verbose_name_plural = "Categories"
        # Alphabetical ordering so paginated lists are always stable
        ordering = ["name"]


# =============================================================================
# Complaint Model
# Represents a single complaint submitted by a user
# =============================================================================
class Complaint(models.Model):

    # -------------------------------------------------------------------------
    # Choice classes — defined at the top before any fields
    # -------------------------------------------------------------------------

    class Status(models.TextChoices):
        OPEN        = "open",        "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED    = "resolved",    "Resolved"
        CLOSED      = "closed",      "Closed"

    class Priority(models.TextChoices):
        LOW    = "low",    "Low"
        MEDIUM = "medium", "Medium"
        HIGH   = "high",   "High"
        URGENT = "urgent", "Urgent"

    # -------------------------------------------------------------------------
    # Relationship fields
    # -------------------------------------------------------------------------

    # The user who submitted this complaint
    # SET_NULL: if user account is deleted, complaint history stays intact
    # null=True: required because SET_NULL needs the column to accept null
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="complaints",
    )

    # The category this complaint belongs to
    # PROTECT: prevents accidental deletion of a category that has complaints
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="complaints",
    )

    # -------------------------------------------------------------------------
    # Core fields
    # -------------------------------------------------------------------------

    # Auto-generated unique business ID e.g. CMP-00001
    # editable=False: cannot be manually set, only generated via save()
    complaint_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    # Short summary of the complaint
    subject = models.CharField(max_length=200)

    # Full detailed description of the complaint
    description = models.TextField()

    # Optional image attachment uploaded by the user
    attachment = models.ImageField(
        upload_to="complaints/",
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------
    # Status and priority fields
    # -------------------------------------------------------------------------

    # Current status — defaults to open when complaint is first submitted
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    # Priority assigned by admin — null until admin sets it
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        null=True,
        blank=True,
        default=None,
    )

    # -------------------------------------------------------------------------
    # Admin and timestamp fields
    # -------------------------------------------------------------------------

    # Internal notes by admin — not visible to the user
    admin_notes = models.TextField(blank=True)

    # Automatically set when the complaint is first created
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated every time the complaint is saved
    updated_at = models.DateTimeField(auto_now=True)

    # Set automatically when status changes to resolved, null until then
    resolved_at = models.DateTimeField(null=True, blank=True)

    # -------------------------------------------------------------------------
    # Meta and methods
    # -------------------------------------------------------------------------

    class Meta:
        # Newest complaints first by default
        ordering = ["-created_at"]
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"

    def __str__(self):
        return self.complaint_number

    def save(self, *args, **kwargs):
        # Auto-generate complaint_number on first save only
        # Uses PostgreSQL sequence for safe concurrent number generation
        if not self.complaint_number:
            with connection.cursor() as cursor:
                cursor.execute("SELECT nextval('complaint_number_seq')")
                number = cursor.fetchone()[0]
            self.complaint_number = f"CMP-{number:05d}"
        super().save(*args, **kwargs)


# =============================================================================
# Response Model
# Represents a single message in a complaint's conversation thread
# Both users and admins can add responses
# =============================================================================
class Response(models.Model):

    # CASCADE: if complaint is deleted, its responses are deleted too
    # Responses only exist to describe their parent complaint
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="responses",
    )

    # PROTECT: keep response history even if author account is deleted
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responses",
    )

    # The actual message text
    message = models.TextField()

    # Automatically set when response is created
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Oldest first so conversation reads top to bottom
        ordering = ["created_at"]
        verbose_name = "Response"
        verbose_name_plural = "Responses"

    def __str__(self):
        # Uses complaint_id (already in memory) instead of complaint.complaint_number
        # Avoids an extra database query per row
        return f"Response to complaint {self.complaint_id}"


# =============================================================================
# ActivityLog Model
# Tracks every action performed on a complaint
# Used for full audit trail — status changes, priority sets, responses added
# =============================================================================
class ActivityLog(models.Model):

    # -------------------------------------------------------------------------
    # Action choices
    # -------------------------------------------------------------------------

    class Action(models.TextChoices):
        CREATED        = "created",        "Created"
        STATUS_CHANGED = "status_changed", "Status Changed"
        PRIORITY_SET   = "priority_set",   "Priority Set"
        RESPONSE_ADDED = "response_added", "Response Added"

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    # CASCADE: if complaint is deleted, its activity logs are deleted too
    # Activity logs only exist to describe their parent complaint
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )

    # Who performed this action
    # CASCADE: if user is deleted, their activity log entries go too
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )

    # What type of action was performed
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )

    # Previous value before the change (e.g. old status "open")
    old_value = models.CharField(max_length=100, blank=True)

    # New value after the change (e.g. new status "in_progress")
    new_value = models.CharField(max_length=100, blank=True)

    # Automatically set when log entry is created
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Most recent activity first
        ordering = ["-timestamp"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        # Uses complaint_id (already in memory) instead of complaint.complaint_number
        # Avoids an extra database query per row
        return f"{self.action} - complaint {self.complaint_id}"
