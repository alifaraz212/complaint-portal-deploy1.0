from django.contrib import admin
from .models import Category, Complaint, Response, ActivityLog

admin.site.register(Category)
admin.site.register(Complaint)
admin.site.register(Response)
admin.site.register(ActivityLog)
