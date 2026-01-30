from django.urls import path, include

urlpatterns = [
    path("accounts/", include('api.v1.accounts.urls')),
    path("projects/", include('api.v1.projects.urls')),
    path("auth/", include('api.v1.auth.urls')),
    path("tasks/", include('api.v1.tasks.urls')),
    path("calendar/events/", include('api.v1.Calendar.urls'))
]