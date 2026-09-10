"""
Root URL configuration for the Complaint Portal.

Routes:
- /admin/      — Django admin
- /api/auth/   — Authentication (register, login, profile)
- /api/complaints/ — Complaint CRUD operations
- /api/dashboard/  — Dashboard statistics
- /media/      — Protected media files (auth + ownership required)
- /static/     — Static files (Django admin CSS/JS)
"""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path
from django.views.static import serve
from rest_framework_simplejwt.authentication import JWTAuthentication


def protected_media(request, path):
    """
    Serve media files only to authenticated users who own the attachment
    or are admins.

    Flow:
    1. Validate JWT token from Authorization header
    2. Look up the ComplaintAttachment by file path
    3. Check user is the complaint owner or an admin
    4. Stream the file if allowed, 401/403 otherwise
    """
    from django.http import JsonResponse

    def cors_response(data, status):
        """Add CORS headers to error responses so browser doesn't swallow them."""
        resp = JsonResponse(data, status=status)
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin in ['http://localhost:3000', 'http://127.0.0.1:3000']:
            resp['Access-Control-Allow-Origin'] = origin
            resp['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return resp

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        resp = cors_response({}, 200)
        resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        return resp

    # Step 1: Authenticate via JWT
    try:
        auth = JWTAuthentication()
        result = auth.authenticate(request)
        if result is None:
            return cors_response({"error": "Authentication required."}, 401)
        user, _ = result
    except Exception:
        return cors_response({"error": "Authentication required."}, 401)

    # Step 2: Look up attachment by file path
    from complaints.models import ComplaintAttachment
    try:
        attachment = ComplaintAttachment.objects.select_related(
            "complaint__user"
        ).get(file=path)
    except ComplaintAttachment.DoesNotExist:
        raise Http404

    # Step 3: Check ownership or admin
    complaint = attachment.complaint
    if user.role != "admin" and complaint.user != user:
        return cors_response({"error": "Access denied."}, 403)

    # Step 4: Stream the file
    full_path = settings.MEDIA_ROOT / path
    if not full_path.exists():
        raise Http404

    return FileResponse(open(full_path, "rb"))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/complaints/", include("complaints.urls")),
    path('api/dashboard/', include('dashboard.urls')),
    # Protected media — requires auth and ownership
    path('media/<path:path>', protected_media),
    # Static files for Django admin (CSS/JS)
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
]