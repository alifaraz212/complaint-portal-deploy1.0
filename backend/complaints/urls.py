"""
Complaints URL configuration.

Provides:
- /api/complaints/categories/              — List (auth) / Create (admin)
- /api/complaints/categories/{id}/         — Detail / Update / Deactivate (admin)
- /api/complaints/complaints/              — List (filtered) / Create (user)
- /api/complaints/complaints/{id}/         — Detail (owner/admin)
- /api/complaints/complaints/{id}/update/  — Update status/priority (admin)
- /api/complaints/complaints/{id}/delete/  — Soft-delete/close (admin)
- /api/complaints/complaints/{id}/responses/  — List / Add responses (owner/admin)
- /api/complaints/complaints/{id}/activity/   — Activity log (admin)
"""

from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    # Categories
    path(
        "categories/",
        views.CategoryListView.as_view(),
        name="category-list",
    ),
    path(
        "categories/create/",
        views.CategoryCreateView.as_view(),
        name="category-create",
    ),
    path(
        "categories/<int:pk>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    # Complaints
    path(
        "complaints/",
        views.ComplaintListCreateView.as_view(),
        name="complaint-list-create",
    ),
    path(
        "complaints/<int:pk>/",
        views.ComplaintDetailView.as_view(),
        name="complaint-detail",
    ),
    path(
        "complaints/<int:pk>/update/",
        views.ComplaintUpdateView.as_view(),
        name="complaint-update",
    ),
    path(
        "complaints/<int:pk>/delete/",
        views.ComplaintDeleteView.as_view(),
        name="complaint-delete",
    ),
    # Responses (nested under complaints)
    path(
        "complaints/<int:complaint_pk>/responses/",
        views.ResponseListCreateView.as_view(),
        name="response-list-create",
    ),
    # Attachments (nested under complaints)
    path(
        "complaints/<int:complaint_pk>/attachments/",
        views.AttachmentListCreateView.as_view(),
        name="attachment-list-create",
    ),
    # Activity log (nested under complaints)
    path(
        "complaints/<int:complaint_pk>/activity/",
        views.ActivityLogListView.as_view(),
        name="activity-log-list",
    ),
]
