"""
Root URL configuration for the Complaint Portal.

Routes:
- /admin/      — Django admin
- /api/auth/   — Authentication (register, login, profile)
- /api/complaints/ — Complaint CRUD operations
- /api/dashboard/  — Dashboard statistics
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from django.views.static import serve
import re

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/complaints/", include("complaints.urls")),
    path('api/dashboard/', include('dashboard.urls')),
    # Serve media files regardless of DEBUG setting
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    # Serve static files regardless of DEBUG setting
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
]