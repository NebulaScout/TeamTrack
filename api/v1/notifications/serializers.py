from rest_framework import serializers

from notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "actor",
            "project",
            "audit_log",
            "category",
            "title",
            "message",
            "action_url",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "actor",
            "project",
            "audit_log",
            "category",
            "title",
            "message",
            "action_url",
            "metadata",
            "read_at",
            "created_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "enabled",
            "muted_modules",
            "muted_action_types",
            "muted_project_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
