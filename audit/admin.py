from django.contrib import admin
from .models import GlobalAuditLog


@admin.register(GlobalAuditLog)
class GlobalAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "module",
        "action",
        "actor",
        "target_type",
        "target_id",
        "project",
        "occurred_at",
    )
    list_filter = ("module", "action", "occurred_at")
    search_fields = ("description", "target_label", "target_type", "actor__username")
    ordering = ("-occurred_at",)
