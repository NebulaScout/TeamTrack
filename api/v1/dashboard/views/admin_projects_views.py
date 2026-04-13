from rest_framework import status
from drf_spectacular.utils import extend_schema

from django.db.models import Count, Q
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.v1.common.responses import ResponseMixin
from core.services.project_service import ProjectService
from projects.models import ProjectsModel
from ..serializers.admin_serializers import (
    AdminProjectListSerializer,
    AdminProjectMemberSerializer,
    AdminProjectWriteSerializer,
)
from core.services.audit_service import AuditService
from core.services.enums import StatusEnum, AuditModule


class AdminProjectMembersView(ResponseMixin, APIView):
    """
    GET /dashboard/admin/projects/<int:pk>/members/
    Returns members for a specific project
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @extend_schema(responses=AdminProjectMemberSerializer)
    def get(self, request, pk):
        try:
            project = ProjectsModel.objects.prefetch_related(
                "members",
                "members__project_member",
                "members__project_member__profile",
            ).get(pk=pk)
        except ProjectsModel.DoesNotExist:
            return self._error(
                code="NOT_FOUND",
                message="Project not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        memberships = project.members.all()
        serializer = AdminProjectMemberSerializer(
            memberships, many=True, context={"request": request}
        )

        return self._success(
            data=serializer.data,
            message="Project members retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class AdminProjectsView(ResponseMixin, APIView):
    """
    GET  /dashboard/admin/projects/   — list all projects (search + status filter)
    POST /dashboard/admin/projects/   — create a new project
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _base_queryset(self):
        return (
            ProjectsModel.objects.select_related("created_by", "created_by__profile")
            .prefetch_related(
                "members",
                "members__project_member",
                "members__project_member__profile",
            )
            .annotate(
                tasks_total=Count("project_tasks", distinct=True),
                tasks_completed=Count(
                    "project_tasks",
                    filter=Q(project_tasks__status=StatusEnum.DONE),
                    distinct=True,
                ),
                member_count=Count("members", distinct=True),
            )
            .order_by("-created_at")
        )

    @extend_schema(responses=AdminProjectListSerializer(many=True))
    def get(self, request):
        queryset = self._base_queryset()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(project_name__icontains=search)

        status_filter = request.query_params.get("status", "").strip().upper()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = AdminProjectListSerializer(
            queryset, many=True, context={"request": request}
        )
        return self._success(
            data=serializer.data, message="Projects retrieved successfully"
        )

    @extend_schema(
        request=AdminProjectWriteSerializer,
        responses={201: AdminProjectListSerializer},
    )
    def post(self, request):
        serializer = AdminProjectWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid project data. Please check all required fields.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        project = ProjectService.create_project(
            user=request.user, data=serializer.validated_data
        )

        annotated = self._base_queryset().get(pk=project.pk)
        serializer = AdminProjectListSerializer(annotated, context={"request": request})
        return self._success(
            data=serializer.data,
            message="Project created successfully",
            status_code=status.HTTP_201_CREATED,
        )


class AdminProjectDetailView(ResponseMixin, APIView):
    """
    GET    /dashboard/admin/projects/<pk>/  — project detail
    PATCH  /dashboard/admin/projects/<pk>/  — update project fields
    DELETE /dashboard/admin/projects/<pk>/  — delete project
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def _get_project(self, pk):
        try:
            return (
                ProjectsModel.objects.select_related(
                    "created_by", "created_by__profile"
                )
                .prefetch_related(
                    "members",
                    "members__project_member",
                    "members__project_member__profile",
                )
                .annotate(
                    tasks_total=Count("project_tasks", distinct=True),
                    tasks_completed=Count(
                        "project_tasks",
                        filter=Q(project_tasks__status=StatusEnum.DONE),
                        distinct=True,
                    ),
                    member_count=Count("members", distinct=True),
                )
                .get(pk=pk)
            )
        except ProjectsModel.DoesNotExist:
            return None

    @extend_schema(responses=AdminProjectListSerializer)
    def get(self, request, pk):
        project = self._get_project(pk)
        if not project:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdminProjectListSerializer(project, context={"request": request})
        return self._success(data=serializer.data)

    @extend_schema(
        request=AdminProjectWriteSerializer,
        responses=AdminProjectListSerializer,
    )
    def patch(self, request, pk):
        project = self._get_project(pk)
        if not project:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        before = {
            "project_name": project.project_name,
            "description": project.description,
            "status": str(project.status) if project.status else "",
            "priority": str(project.priority) if project.priority else "",
            "start_date": str(project.start_date) if project.start_date else "",
            "end_date": str(project.end_date) if project.end_date else "",
        }

        serializer = AdminProjectWriteSerializer(
            project, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid project data",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        updated = self._get_project(pk)
        if not updated:
            return self._error(
                "NOT_FOUND",
                "Project not found after update",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        after = {
            "project_name": updated.project_name,
            "description": updated.description,
            "status": str(updated.status) if updated.status else "",
            "priority": str(updated.priority) if updated.priority else "",
            "start_date": str(updated.start_date) if updated.start_date else "",
            "end_date": str(updated.end_date) if updated.end_date else "",
        }

        changed_fields = {}

        for field, old_value in before.items():
            new_value = after[field]
            if old_value != new_value:
                changed_fields[field] = {"old": old_value, "new": new_value}

        if changed_fields:
            AuditService.updated(
                module=AuditModule.PROJECT,
                actor=request.user,
                target=updated,
                project=updated,
                description=f'Updated project "{updated.project_name}"',
                metadata={"changes": changed_fields},
            )

        out = AdminProjectListSerializer(updated, context={"request": request})
        return self._success(data=out.data, message="Project updated successfully")

    def delete(self, request, pk):
        try:
            project = ProjectsModel.objects.get(pk=pk)
        except ProjectsModel.DoesNotExist:
            return self._error(
                "NOT_FOUND",
                "Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        project_id = project.pk
        project_name = project.project_name

        AuditService.deleted(
            module=AuditModule.PROJECT,
            actor=request.user,
            target_type=ProjectsModel.__name__,
            target_id=project_id,
            target_label=project_name,
            project=project,
            description=f'Deleted project "{project_name}"',
            metadata={"project_name": project_name},
        )
        project.delete()
        return self._success(
            message="Project deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )
