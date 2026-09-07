"""
Root URL configuration for the Complaint Portal.

Routes:
- /admin/      — Django admin
- /api/auth/   — Authentication (register, login, profile)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/complaints/", include("complaints.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
