from django.urls import path

from .views import (
    DashboardView,
    AdminQuickActionsView,
    AdminUserDetailView,
    AdminUsersView,
    AdminProjectsView,
    AdminProjectDetailView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("admin/", AdminQuickActionsView.as_view(), name="admin-quick-actions"),
    path("admin/users/", AdminUsersView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"
    ),
    path("admin/projects/", AdminProjectsView.as_view(), name="admin-projects"),
    path(
        "admin/projects/<int:pk>/",
        AdminProjectDetailView.as_view(),
        name="admin-project-detail",
    ),
]
