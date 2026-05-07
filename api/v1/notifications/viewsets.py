from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from notifications.models import Notification, NotificationPreference
from core.services.permissions import NotificationPermissions
from typing import cast
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [NotificationPermissions]
    serializer_class = NotificationSerializer

    def get_queryset(self):  # type: ignore
        qs = Notification.objects.filter(recipient=self.request.user).select_related(
            "actor", "project", "audit_log"
        )
        request = cast(Request, self.request)
        is_read = request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=str(is_read).lower() == "true")
        return qs

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response({"status": "read"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unread")
    def mark_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_unread()
        return Response({"status": "unread"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"status": "read_all"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [NotificationPermissions]
    serializer_class = NotificationPreferenceSerializer

    def get_queryset(self):  # type: ignore
        return NotificationPreference.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(pref, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
