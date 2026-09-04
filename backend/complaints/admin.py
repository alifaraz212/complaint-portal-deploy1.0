from django.contrib import admin
from .models import Category, Complaint, Response, ActivityLog, ComplaintAttachment

# ─────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


# ─────────────────────────────────────────────────────────────────────
# Complaint
# ─────────────────────────────────────────────────────────────────────

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ["complaint_number", "user", "status", "priority", "created_at"]
    list_filter = ["status", "priority", "category", "created_at"]
    search_fields = ["complaint_number", "subject", "user__email"]
    readonly_fields = ["complaint_number", "created_at", "updated_at", "resolved_at"]

    # Override single record deletion — sets is_archived=True instead of deleting
    # Called when admin clicks delete on a single complaint
    def delete_model(self, request, obj):
        obj.is_archived = True
        obj.save()

    # Override bulk deletion — called when admin selects multiple complaints and deletes
    # queryset.delete() bypasses delete_model so we need this separately
    def delete_queryset(self, request, queryset):
        queryset.update(is_archived=True)


# ─────────────────────────────────────────────────────────────────────
# Response
# ─────────────────────────────────────────────────────────────────────

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ["id", "complaint", "author", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["complaint__complaint_number", "author__email", "message"]
    readonly_fields = ["created_at"]


# ─────────────────────────────────────────────────────────────────────
# ActivityLog
# ─────────────────────────────────────────────────────────────────────

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["complaint", "action", "performed_by", "timestamp"]
    list_filter = ["action", "timestamp"]
    search_fields = ["complaint__complaint_number", "performed_by__email"]
    readonly_fields = ["timestamp"]


# ─────────────────────────────────────────────────────────────────────
# ComplaintAttachment
# ─────────────────────────────────────────────────────────────────────

@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "complaint", "uploaded_at"]
    list_filter = ["uploaded_at"]
    search_fields = ["complaint__complaint_number"]
    readonly_fields = ["uploaded_at"]

