from django.urls import path

from .views import DashboardView, AdminQuickActions

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("admin/", AdminQuickActions.as_view(), name="admin-quick-actions"),
]
