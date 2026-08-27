from django.db import models, connection
from django.conf import settings


# --- Category Model ---
# Represents the type/category of a complaint (e.g. Billing, Technical)
class Category(models.Model):
    # Name of the category, must be unique
    name = models.CharField(max_length=100, unique=True)
    # Optional description of what this category covers
    description = models.TextField(blank=True)
    # Admin can deactivate a category without deleting it
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# --- Complaint Model ---
# Represents a single complaint submitted by a user
class Complaint(models.Model):

    # --- Inner choice classes defined at the top before any fields ---

    # Possible statuses a complaint can be in
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    # Possible priority levels assigned by admin
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    # --- Fields ---

    # The user who submitted this complaint
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="complaints",
    )

    # The category this complaint belongs to
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="complaints",
    )

    # Auto-generated unique ID e.g. CMP-00001 (set in save() method)
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

    # Current status of the complaint, defaults to open
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    # Priority level assigned by admin, optional until admin sets it
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        null=True,
        blank=True,
        default=None,
    )

    # Internal notes by admin, not visible to the user
    admin_notes = models.TextField(blank=True)

    # Automatically set when the complaint is first created
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated every time the complaint is saved
    updated_at = models.DateTimeField(auto_now=True)

    # Set when status changes to resolved, null until then
    resolved_at = models.DateTimeField(null=True, blank=True)

    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"

    def __str__(self):
        return self.complaint_number

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT nextval('complaint_number_seq')"
                )
                number = cursor.fetchone()[0]

            self.complaint_number = f"CMP-{number:05d}"

        super().save(*args, **kwargs)


class Response(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.PROTECT,
        related_name="responses",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responses",
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Response"
        verbose_name_plural = "Responses"

    def __str__(self):
        return f"Response to {self.complaint.complaint_number}"


class ActivityLog(models.Model):

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        STATUS_CHANGED = "status_changed", "Status Changed"
        PRIORITY_SET = "priority_set", "Priority Set"
        RESPONSE_ADDED = "response_added", "Response Added"

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.PROTECT,
        related_name="activity_logs",
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="activity_logs",
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )

    old_value = models.CharField(
        max_length=100,
        blank=True,
    )

    new_value = models.CharField(
        max_length=100,
        blank=True,
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.action} - {self.complaint.complaint_number}"
