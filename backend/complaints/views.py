"""
Complaint views.

Handles category CRUD, complaint CRUD, responses, and activity logs.
Uses DRF viewsets and generic views with proper permission classes.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from accounts.permissions import IsAdmin, IsOwnerOrAdmin

from .filters import ComplaintFilter
from .models import ActivityLog, Category, Complaint
from .models import Response as ComplaintResponse
from .models import ComplaintAttachment
from .serializers import (
    ActivityLogSerializer,
    CategorySerializer,
    ComplaintAttachmentSerializer,
    ComplaintCreateSerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    ComplaintUpdateSerializer,
    ResponseSerializer,
)


# ─────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    """
    Standard pagination for list views.

    Defaults to 10 items per page, configurable via ?page_size=N.
    Maximum 100 to prevent abuse.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# ─────────────────────────────────────────────────────────────────────
# Category views
# ─────────────────────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    """
    GET /api/complaints/categories/

    List active categories. Available to all authenticated users.
    Admin sees all categories (including inactive).
    """

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Category.objects.all()
        return Category.objects.filter(is_active=True)


class CategoryCreateView(generics.CreateAPIView):
    """
    POST /api/complaints/categories/

    Create a new category. Admin only.
    """

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Category.objects.all()


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/complaints/categories/{id}/

    Admin only.
    DELETE deactivates the category (soft delete via is_active=False)
    rather than hard-deleting, because PROTECT on Complaint.category
    would block deletion if any complaints reference it.
    """

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Category.objects.all()

    def perform_destroy(self, instance):
        """Soft-delete: deactivate instead of deleting."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return DRFResponse(
            {"message": f"Category '{instance.name}' has been deactivated."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────
# Complaint views
# ─────────────────────────────────────────────────────────────────────

class ComplaintListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/complaints/complaints/  — List complaints (filtered by ownership for users)
    POST /api/complaints/complaints/  — Submit a new complaint

    Supports filtering, search, ordering, and pagination.

    Queryset:
    - Regular users see only their own complaints.
    - Admins see all complaints.

    Uses select_related to prevent N+1 queries on category and user.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ComplaintFilter
    ordering_fields = ["created_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ComplaintCreateSerializer
        return ComplaintListSerializer

    def get_queryset(self):
        qs = Complaint.objects.select_related("category", "user")
        if self.request.user.role == "admin":
            return qs
        return qs.filter(user=self.request.user)


class ComplaintDetailView(generics.RetrieveAPIView):
    """
    GET /api/complaints/complaints/{id}/

    Returns full complaint detail with nested responses and activity logs.

    Permissions:
    - Owner can see their own complaint (without activity logs).
    - Admin can see any complaint (with activity logs).

    Uses prefetch_related to prevent N+1 on responses and activity_logs.
    """

    serializer_class = ComplaintDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return Complaint.objects.select_related(
            "category", "user"
        ).prefetch_related(
            "responses__author",
            "activity_logs__performed_by",
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Regular users should not see activity logs or admin_notes
        if request.user.role != "admin":
            data.pop("activity_logs", None)
            data.pop("admin_notes", None)

        return DRFResponse(data)


class ComplaintUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/complaints/complaints/{id}/update/

    Admin: can change status, priority, admin_notes.
    Regular user: limited updates (currently none via this endpoint).

    Status changes are validated against the workflow rules in the
    service layer. Every change is logged in ActivityLog.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Complaint.objects.select_related("category", "user")

    def get_serializer_class(self):
        return ComplaintUpdateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Pass the complaint instance to the serializer for status validation
        if self.kwargs.get("pk"):
            context["complaint"] = self.get_object()
        return context

    def update(self, request, *args, **kwargs):
        complaint = self.get_object()
        serializer = ComplaintUpdateSerializer(
            data=request.data,
            context={"request": request, "complaint": complaint},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.update(complaint, serializer.validated_data)

        # Return the full detail view of the updated complaint
        detail_serializer = ComplaintDetailSerializer(updated)
        return DRFResponse(detail_serializer.data)


class ComplaintDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/complaints/complaints/{id}/delete/

    Admin only. Soft-deletes by setting status to 'closed'.
    Hard deletion is not supported to preserve audit trail.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Complaint.objects.all()

    def perform_destroy(self, instance):
        """Soft-close instead of hard-delete."""
        if instance.status != Complaint.Status.CLOSED:
            instance.status = Complaint.Status.CLOSED
            instance.save(update_fields=["status", "updated_at"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return DRFResponse(
            {"message": f"Complaint {instance.complaint_number} has been closed."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────
# Attachment views (nested under complaints)
# ─────────────────────────────────────────────────────────────────────

class AttachmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/complaints/complaints/{complaint_pk}/attachments/ — List attachments
    POST /api/complaints/complaints/{complaint_pk}/attachments/ — Upload attachment

    Both owner and admin can upload attachments to a complaint.
    """

    serializer_class = ComplaintAttachmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_complaint(self):
        """
        Retrieve the parent complaint and check permissions.

        - Owner can access their own complaint's attachments.
        - Admin can access any complaint's attachments.
        """
        complaint = generics.get_object_or_404(
            Complaint.objects.select_related("user"),
            pk=self.kwargs["complaint_pk"],
        )
        # Check ownership or admin
        if (
            self.request.user.role != "admin"
            and complaint.user != self.request.user
        ):
            self.permission_denied(self.request)
        return complaint

    def get_queryset(self):
        complaint = self.get_complaint()
        return ComplaintAttachment.objects.filter(
            complaint=complaint
        ).order_by("-uploaded_at")

    def perform_create(self, serializer):
        """Attach the complaint to the uploaded file."""
        complaint = self.get_complaint()
        serializer.save(complaint=complaint)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["complaint"] = self.get_complaint()
        return context


# ─────────────────────────────────────────────────────────────────────
# Response views (nested under complaints)
# ─────────────────────────────────────────────────────────────────────

class ResponseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/complaints/complaints/{complaint_pk}/responses/ — List responses for a complaint
    POST /api/complaints/complaints/{complaint_pk}/responses/ — Add a response

    Both owner and admin can add responses (back-and-forth conversation).
    """

    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_complaint(self):
        """
        Retrieve the parent complaint and check permissions.

        - Owner can access their own complaint's responses.
        - Admin can access any complaint's responses.
        """
        complaint = generics.get_object_or_404(
            Complaint.objects.select_related("user"),
            pk=self.kwargs["complaint_pk"],
        )
        # Check ownership or admin
        if (
            self.request.user.role != "admin"
            and complaint.user != self.request.user
        ):
            self.permission_denied(self.request)
        return complaint

    def get_queryset(self):
        complaint = self.get_complaint()
        return ComplaintResponse.objects.filter(
            complaint=complaint
        ).select_related("author")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["complaint"] = self.get_complaint()
        return context


# ─────────────────────────────────────────────────────────────────────
# Activity log views (nested under complaints)
# ─────────────────────────────────────────────────────────────────────

class ActivityLogListView(generics.ListAPIView):
    """
    GET /api/complaints/complaints/{complaint_pk}/activity/

    Admin only. Returns the full activity history for a complaint.
    """

    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        return ActivityLog.objects.filter(
            complaint_id=self.kwargs["complaint_pk"]
        ).select_related("performed_by")
