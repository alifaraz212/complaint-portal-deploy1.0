"""
Accounts URL configuration.

Provides:
- POST /api/auth/register/        — User registration (public)
- POST /api/auth/login/           — JWT token obtain (public)
- POST /api/auth/refresh/         — JWT token refresh (public)
- GET/PUT /api/auth/profile/      — User profile (authenticated)
- POST /api/auth/change-password/ — Change password (authenticated)
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]
