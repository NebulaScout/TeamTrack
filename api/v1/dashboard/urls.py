from django.urls import path

from .views.users_views import DashboardView
from .views.admin_users_views import AdminUsersView, AdminUserDetailView
from .views.admin_projects_views import (
    AdminProjectsView,
    AdminProjectDetailView,
    AdminProjectMembersView,
)
from .views.admin_tasks_views import (
    AdminQuickActionsView,
    AdminTasksView,
    AdminTaskDetailView,
)
from .views.admin_audit_views import AdminAuditLogsView


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
    path(
        "admin/projects/<int:pk>/members/",
        AdminProjectMembersView.as_view(),
        name="admin-project-members",
    ),
    path("admin/tasks/", AdminTasksView.as_view(), name="admin-tasks"),
    path(
        "admin/tasks/<int:pk>/", AdminTaskDetailView.as_view(), name="admin-task-detail"
    ),
    path("admin/audit-logs/", AdminAuditLogsView.as_view(), name="admin-audit-logs"),
]
