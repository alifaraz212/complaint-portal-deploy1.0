"""
Custom permission classes for the Complaint Portal.

These permissions work alongside DRF's built-in IsAuthenticated.
They check the user's 'role' field on the custom User model.
"""

from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to users with role == 'admin'.

    This is distinct from Django's is_staff / is_superuser flags.
    The 'role' field is an application-level concept used for
    business logic (e.g., who can change complaint status/priority).

    Usage:
        permission_classes = [IsAuthenticated, IsAdmin]
    """

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )

class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allows access if the user owns the object
    or is an admin.

    Requires the object to have a 'user' attribute (e.g., Complaint.user).
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj.user == request.user
