"""
Complaint business logic service layer.

Centralizes business rules so they are enforced regardless of whether
changes come from the API, admin, or management commands.

Key rules:
- Status transitions follow a strict workflow.
- Every change is logged in ActivityLog.
- resolved_at is auto-set when status becomes 'resolved'.
- Only admins can change status and priority.
"""

from django.db import transaction
from django.utils import timezone

from .models import ActivityLog, Complaint, Response


# ─────────────────────────────────────────────────────────────────────
# Status workflow rules
# ─────────────────────────────────────────────────────────────────────

# Maps each status to its allowed next statuses.
# "closed" has no transitions — it is a terminal state.
ALLOWED_TRANSITIONS = {
    "open": {"in_progress"},
    "in_progress": {"resolved", "open"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),  # Terminal — no further changes
}


def validate_status_transition(current_status, new_status):
    """
    Check if a status transition is allowed.

    Returns:
        (is_valid: bool, error_message: str | None)
    """
    if current_status == new_status:
        return True, None

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        allowed_str = ", ".join(sorted(allowed)) if allowed else "none"
        return False, (
            f"Cannot change status from '{current_status}' to '{new_status}'. "
            f"Allowed transitions from '{current_status}': {allowed_str}."
        )
    return True, None


# ─────────────────────────────────────────────────────────────────────
# Complaint creation
# ─────────────────────────────────────────────────────────────────────

@transaction.atomic
def create_complaint(*, user, category, subject, description):
    """
    Create a new complaint and log the creation.

    Uses transaction.atomic so if the ActivityLog fails,
    the complaint creation is rolled back too.
    
    Note: Attachments are handled separately via ComplaintAttachment model
    """
    complaint = Complaint(
        user=user,
        category=category,
        subject=subject,
        description=description,
        status=Complaint.Status.OPEN,
    )
    complaint.save()

    ActivityLog.objects.create(
        complaint=complaint,
        performed_by=user,
        action="created",
        old_value="",
        new_value="open",
    )

    return complaint


# ─────────────────────────────────────────────────────────────────────
# Complaint update (admin operations)
# ─────────────────────────────────────────────────────────────────────

@transaction.atomic
def update_complaint_status(*, complaint, new_status, performed_by):
    """
    Change a complaint's status following workflow rules.

    Business rules:
    - Only allowed transitions are permitted.
    - resolved_at is auto-set when status becomes 'resolved'.
    - resolved_at is cleared if status moves away from 'resolved'.
    - Every change is logged in ActivityLog.

    Uses select_for_update() to prevent concurrent race conditions where
    two simultaneous requests could both validate against stale data.

    Raises:
        ValueError: If the transition is not allowed.
    """
    # Lock the row for the duration of this transaction to prevent concurrent updates
    complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
    
    old_status = complaint.status

    if old_status == new_status:
        return complaint  # No change needed

    is_valid, error = validate_status_transition(old_status, new_status)
    if not is_valid:
        raise ValueError(error)

    complaint.status = new_status

    # Auto-manage resolved_at timestamp
    if new_status == Complaint.Status.RESOLVED:
        complaint.resolved_at = timezone.now()
    elif old_status == Complaint.Status.RESOLVED and new_status == Complaint.Status.IN_PROGRESS:
        # Only clear resolved_at when moving BACKWARDS (resolved → in_progress)
        # NOT when moving forwards (resolved → closed) — we want to keep the timestamp
        complaint.resolved_at = None

    complaint.save(update_fields=["status", "resolved_at", "updated_at"])

    ActivityLog.objects.create(
        complaint=complaint,
        performed_by=performed_by,
        action="status_changed",
        old_value=old_status,
        new_value=new_status,
    )

    return complaint


@transaction.atomic
def update_complaint_priority(*, complaint, new_priority, performed_by):
    """
    Set or change a complaint's priority.

    Logs the change in ActivityLog with old and new values.
    """
    old_priority = complaint.priority or ""

    if old_priority == new_priority:
        return complaint  # No change needed

    complaint.priority = new_priority
    complaint.save(update_fields=["priority", "updated_at"])

    ActivityLog.objects.create(
        complaint=complaint,
        performed_by=performed_by,
        action="priority_set",
        old_value=old_priority,
        new_value=new_priority,
    )

    return complaint


# ─────────────────────────────────────────────────────────────────────
# Response (conversation thread)
# ─────────────────────────────────────────────────────────────────────

@transaction.atomic
def add_response(*, complaint, author, message):
    """
    Add a response to a complaint's conversation thread.

    Both users and admins can add responses.
    Each response is logged in ActivityLog.
    """
    response = Response.objects.create(
        complaint=complaint,
        author=author,
        message=message,
    )

    ActivityLog.objects.create(
        complaint=complaint,
        performed_by=author,
        action="response_added",
        old_value="",
        new_value=f"Response #{response.id}",
    )

    return response
