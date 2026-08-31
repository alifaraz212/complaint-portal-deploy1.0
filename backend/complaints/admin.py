from django.contrib import admin
from .models import Category, Complaint, Response, ActivityLog, ComplaintAttachment

# Category, Response, ActivityLog, ComplaintAttachment use plain registration
# They don't have is_archived so no soft delete override needed
admin.site.register(Category)
admin.site.register(Response)
admin.site.register(ActivityLog)
admin.site.register(ComplaintAttachment)


# Complaint has soft delete — override delete actions
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):

    # Override single record deletion — sets is_archived=True instead of deleting
    # Called when admin clicks delete on a single complaint
    def delete_model(self, request, obj):
        obj.is_archived = True
        obj.save()

    # Override bulk deletion — called when admin selects multiple complaints and deletes
    # queryset.delete() bypasses delete_model so we need this separately
    def delete_queryset(self, request, queryset):
        queryset.update(is_archived=True)
