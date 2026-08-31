from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    # Columns shown in the user list page
    list_display = ["email", "full_name", "role", "is_staff", "is_active"]

    # Search by email or full name
    search_fields = ["email", "full_name"]

    # Default ordering in the list
    ordering = ["email"]

    # Fields shown when EDITING an existing user
    # Fully redefined because default fieldsets reference username which we removed
    fieldsets = (
        (None, {
            "fields": ("email", "password")
        }),
        ("Personal Info", {
            "fields": ("full_name", "phone")
        }),
        ("Role", {
            "fields": ("role",)
        }),
        ("Permissions", {
            "fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    # Fields shown when CREATING a new user via admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone", "role", "password1", "password2"),
        }),
    )
    
    # Override single record deletion — sets is_archived=True instead of deleting the row
    # This is called when admin clicks delete on a single user
    def delete_model(self, request, obj):
        obj.is_archived = True
        obj.is_active = False  # also deactivate so archived user cannot log in
        obj.save()

    # Override bulk deletion — called when admin selects multiple users and deletes
    # queryset.delete() would bypass delete_model so we need this separately
    def delete_queryset(self, request, queryset):
        queryset.update(is_archived=True, is_active=False)
