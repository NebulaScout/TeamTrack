from django.urls import path

from .views import (
    DashboardView,
    AdminQuickActionsView,
    AdminUserDetailView,
    AdminUsersView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("admin/", AdminQuickActionsView.as_view(), name="admin-quick-actions"),
    path("admin/users/", AdminUsersView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"
    ),
]
