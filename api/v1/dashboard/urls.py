from django.urls import path

from .views.users_views import (
    DashboardView,
)
from .views.admin_views import (
    AdminQuickActionsView,
    AdminUserDetailView,
    AdminUsersView,
    AdminProjectsView,
    AdminProjectDetailView,
    AdminTaskDetailView,
    AdminTasksView,
    AdminAuditLogsView,
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
    path("admin/tasks/", AdminTasksView.as_view(), name="admin-tasks"),
    path(
        "admin/tasks/<int:pk>/", AdminTaskDetailView.as_view(), name="admin-task-detail"
    ),
    path("admin/audit-logs/", AdminAuditLogsView.as_view(), name="admin-audit-logs"),
    path(
        "admin/tasks/<int:pk>/", AdminTaskDetailView.as_view(), name="admin-task-detail"
    ),
]
