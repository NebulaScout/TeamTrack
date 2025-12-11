from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import web
from .views import api

router = DefaultRouter()
router.register(r'register', api.RegisterViewSet, basename='register-api')

urlpatterns = [
    # Template Views
    path('', web.home, name='home'),
    path('register/', web.register, name='register'),

    # API Routes
    path('api/', include(router.urls)),
]