from rest_framework import viewsets, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Count, Case, When, IntegerField
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from projects.models import ProjectsModel, ProjectMembers
from .serializers import (
    ExtendedUserSerializer,
    ProjectMemberSerializer,
    TaskSerializer,
    ProjectListSerializer,
    ProjectsDetailSerializer,
    ProjectWriteSerializer,
    InviteTeamMemberSerializer,
    ProjectMemberDetailSerializer,
    TeamStatsSerializer,
    UpdateMemberRoleSerializer,
    AddTeamMemberSerializer,
)
from core.services.permissions import ProjectPermissions
from core.services.project_service import ProjectService
from core.services.task_service import TaskService
from core.services.permissions import ROLE_PERMISSIONS
from api.v1.common.responses import ResponseMixin

from tasks.models import TaskModel


class ProjectsViewSet(ResponseMixin, viewsets.ModelViewSet):
    permission_classes = [ProjectPermissions]
    authentication_classes = [JWTAuthentication]
    # serializer_class = ProjectsSerializer

    def get_serializer_class(self):  # type: ignore
        """Return different serializers based on the action"""
        if self.action == "list":
            return ProjectListSerializer
        elif self.action == "retrieve":
            return ProjectsDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProjectWriteSerializer

    def get_queryset(self):  # type: ignore
        user = self.request.user
        user_groups = user.groups.values_list("name", flat=True)

        # Check if user has permission to view all projects
        can_view_all = any(
            "view_projectsmodel" in ROLE_PERMISSIONS.get(group, [])
            for group in user_groups
        )

        # If a user has view_projectsmodel permission, they can view all created projects
        if can_view_all:
            return (
                ProjectsModel.objects.all()
                .distinct()
                .prefetch_related("members", "members__project_member__profile")
                .select_related("created_by")
            )

        return (
            ProjectsModel.objects.filter(  # Return if:
                Q(created_by=user)  # project was created by the user or
                | Q(
                    members__project_member=user
                )  # user has been assigned to the project
            )
            .distinct()  # remove duplicates
            .prefetch_related(
                "members", "members__project_member"
            )  # retrive related records for better performance
            .select_related("created_by")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self._success(
            data=serializer.data, message="Projects retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Error creating project! Please confirm all fields have the necessary data.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        project = ProjectService.create_project(
            user=request.user, data=serializer.validated_data
        )

        output_serializer = self.get_serializer(project)
        return self._success(
            data=output_serializer.data,
            message="Project created successfully",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer(many=True), 201: TaskSerializer()},
        methods=["GET", "POST"],
    )
    @action(detail=True, methods=["post", "get"], url_path="tasks")
    def tasks(self, request, pk=None):
        """Handle tasks for a project"""

        # get project id from the url parameter
        project = self.get_object()

        if request.method == "POST":
            # Create a new task
            serializer = TaskSerializer(data=request.data)
            # serializer.is_valid(raise_exception=True)

            if not serializer.is_valid():
                return self._error(
                    "INVALID_INPUT",
                    "Error creating task! Please confirm all fields have the necessary data.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            task = TaskService.create_task(
                user=request.user, project_id=project.id, data=serializer.validated_data
            )

            # Return serializer response
            output_serializer = TaskSerializer(task)
            return self._success(
                data=output_serializer.data,
                message="Task created successfully",
                status_code=status.HTTP_201_CREATED,
            )

        else:  # GET request
            # List all tasks for this project
            tasks = (
                TaskModel.objects.filter(project=project)
                .select_related("created_by", "assigned_to", "project")
                .prefetch_related(
                    "comments", "comments__author", "history", "history__changed_by"
                )
            )

            serializer = TaskSerializer(tasks, many=True)

            return self._success(
                data=serializer.data, message="Tasks retrieved successfully"
            )

    # TODO: Re-evaluate on whether to add or invite a member

    # @action(detail=True, methods=["post"], url_path="members")
    # def add_members(self, request, pk=None):
    #     project = self.get_object()  # get project id

    #     serializer = ProjectMemberSerializer(
    #         data=request.data, context={"request": request}
    #     )

    #     # serializer.is_valid(raise_exception=True)
    #     if not serializer.is_valid():
    #         return self._error(
    #             "INVALID_INPUT",
    #             "Unable to add member to project!. Please relaod and try again.",
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )
    #     serializer.save(project=project)

    #     return self._success(
    #         data=serializer.data,
    #         message="User added to project.",
    #         status=status.HTTP_201_CREATED,
    #     )

    @extend_schema(
        request=InviteTeamMemberSerializer,
        responses={
            201: ProjectMemberDetailSerializer,
            400: OpenApiResponse(
                description="Bad Request - Invalid data or user already in project"
            ),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="User or Project not found"),
        },
        description="Invite a team member to the project. Only Admins and Project Managers can invite members.",
    )
    @action(detail=True, methods=["post"], url_path="team/invite")
    def invite_team_member(self, request, pk=None):  # TODO: Rename this method
        """
        Invite a user to join the project team.
        Required permissions: Admin or Project Manager
        """
        project = self.get_object()
        serializer = InviteTeamMemberSerializer(data=request.data)

        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid input data",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Find the user by email or username
        user_to_invite = None
        if serializer.validated_data.get("email"):
            user_to_invite = User.objects.filter(
                email=serializer.validated_data["email"]
            ).first()
        elif serializer.validated_data.get("username"):
            user_to_invite = User.objects.filter(
                username=serializer.validated_data["username"]
            ).first()

        if not user_to_invite:
            return self._error(
                "USER_NOT_FOUND",
                "User not found with provided credentials",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Check if user is already a member
        if ProjectMembers.objects.filter(
            project=project, project_member=user_to_invite
        ).exists():
            return self._error(
                "ALREADY_MEMBER",
                f"{user_to_invite.username} is already a member of this project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

            # Create the project membership
        membership = ProjectMembers.objects.create(
            project=project,
            project_member=user_to_invite,
            role_in_project=serializer.validated_data["role"],
        )

        # TODO: Configure to send email notifications
        # send_invitation_email(user_to_invite, project, request.user)

        output_serializer = ProjectMemberDetailSerializer(
            membership, context={"request": request}
        )

        return self._success(
            data=output_serializer.data,
            message=f"{user_to_invite.username} has been added to the project team",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={
            200: ProjectMemberDetailSerializer(many=True),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
        },
        parameters=[
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by role (Admin, Project Manager, Developer, Guest)",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search by username, first name, last name, or email",
                required=False,
            ),
        ],
        description="List all team members for a specific project with optional filtering",
    )
    @action(detail=True, methods=["get"], url_path="team/members")
    def list_team_members(self, request, pk=None):
        project = self.get_object()

        members = (
            ProjectMembers.objects.filter(project=project)
            .select_related("project_member", "project_member__profile")
            .prefetch_related("project_member__assigned_tasks")
        )

        role_filter = request.query_params.get("role")
        if role_filter:
            members = members.filter(role_in_project=role_filter)

        search_query = request.query_params.get("search")
        if search_query:
            members = members.filter(
                Q(project_member__username__icontains=search_query)
                | Q(project_member__first_name__icontains=search_query)
                | Q(project_member__last_name__icontains=search_query)
                | Q(project_member__email__icontains=search_query)
            )

        serializer = ProjectMemberDetailSerializer(
            members, many=True, context={"request": request}
        )
        return self._success(
            data=serializer.data, message="Team members retrieved successfully"
        )

    @extend_schema(
        request=AddTeamMemberSerializer,
        responses={
            201: ProjectMemberDetailSerializer,
            400: OpenApiResponse(
                description="Bad Request - Invalid input or already a member"
            ),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="User not found"),
        },
        description="Add a team member to the project using user_id and role",
    )
    @list_team_members.mapping.post  # type: ignore
    def add_team_member(self, request, pk=None):
        project = self.get_object()

        input_serializer = AddTeamMemberSerializer(data=request.data)
        if not input_serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid input data",
                details=input_serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_to_add = User.objects.get(id=input_serializer.validated_data["user_id"])

        if ProjectMembers.objects.filter(
            project=project, project_member=user_to_add
        ).exists():
            return self._error(
                "ALREADY_MEMBER",
                f"{user_to_add.username} is already a member of this project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        membership = ProjectMembers.objects.create(
            project=project,
            project_member=user_to_add,
            role_in_project=input_serializer.validated_data["role"],
        )

        output_serializer = ProjectMemberDetailSerializer(
            membership, context={"request": request}
        )

        return self._success(
            data=output_serializer.data,
            message=f"{user_to_add.username} has been added to the project team",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={
            200: TeamStatsSerializer,
        },
        description="Get statistics about the project team",
    )
    @action(detail=True, methods=["get"], url_path="team/stats")
    def team_stats(self, request, pk=None):
        """Get statistics about the project team"""
        project = self.get_object()

        members = ProjectMembers.objects.filter(project=project).select_related(
            "project_member", "project_member__profile"
        )

        # Calculate statistics
        from django.utils import timezone
        from datetime import timedelta

        online_threshold = timezone.now() - timedelta(minutes=5)

        stats = {
            "total_members": members.count(),
            "online_members": members.filter(
                project_member__profile__last_seen__gte=online_threshold
            ).count(),
            "admins": members.filter(role_in_project="Admin").count(),
            "project_managers": members.filter(
                role_in_project="Project Manager"
            ).count(),
            "developers": members.filter(role_in_project="Developer").count(),
            "guests": members.filter(role_in_project="Guest").count(),
        }

        return self._success(
            data=stats, message="Team statistics retrieved successfully"
        )

    @extend_schema(
        request=UpdateMemberRoleSerializer,
        responses={
            200: ProjectMemberDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Member not found"),
        },
        description="Update a team member's role in the project. Only Admins and Project Managers can update roles.",
    )
    @action(
        detail=True,
        methods=["patch"],
        url_path="team/members/(?P<member_id>[^/.]+)/role",
    )
    def update_member_role(self, request, pk=None, member_id=None):
        """
        Update a team member's role in the project.
        Required permissions: Admin or Project Manager
        """
        project = self.get_object()

        # Get the membership
        try:
            membership = ProjectMembers.objects.select_related(
                "project_member", "project_member__profile"
            ).get(project=project, project_member_id=member_id)
        except ProjectMembers.DoesNotExist:
            return self._error(
                "MEMBER_NOT_FOUND",
                "Team member not found in this project",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Prevent users from changing their own role
        if membership.project_member == request.user:
            return self._error(
                "INVALID_OPERATION",
                "You cannot change your own role",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdateMemberRoleSerializer(data=request.data)

        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid role specified",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Update the role
        old_role = membership.role_in_project
        membership.role_in_project = serializer.validated_data["role"]
        membership.save()

        output_serializer = ProjectMemberDetailSerializer(
            membership, context={"request": request}
        )

        return self._success(
            data=output_serializer.data,
            message=f"Role updated from {old_role} to {membership.role_in_project}",
        )

    @extend_schema(
        request=UpdateMemberRoleSerializer,
        responses={
            200: ProjectMemberDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Member not found"),
        },
        description="Update a team member role using uppercase role payload",
    )
    @action(
        detail=True,
        methods=["patch"],
        url_path="team/members/(?P<member_id>[^/.]+)",
    )
    def update_team_member(self, request, pk=None, member_id=None):
        project = self.get_object()

        try:
            membership = ProjectMembers.objects.select_related(
                "project_member", "project_member__profile"
            ).get(project=project, project_member_id=member_id)
        except ProjectMembers.DoesNotExist:
            return self._error(
                "MEMBER_NOT_FOUND",
                "Team member not found in this project",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if membership.project_member == request.user:
            return self._error(
                "INVALID_OPERATION",
                "You cannot change your own role",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdateMemberRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error(
                "INVALID_INPUT",
                "Invalid role specified",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        old_role = membership.role_in_project
        membership.role_in_project = serializer.validated_data["role"]
        membership.save()

        output_serializer = ProjectMemberDetailSerializer(
            membership, context={"request": request}
        )

        return self._success(
            data=output_serializer.data,
            message=f"Role updated from {old_role} to {membership.role_in_project}",
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Member removed successfully"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Member not found"),
        },
        description="Remove a team member from the project. Only Admins and Project Managers can remove members.",
    )
    @update_team_member.mapping.delete  # type: ignore
    def remove_team_member(self, request, pk=None, member_id=None):
        """
        Remove a team member from the project.
        Required permissions: Admin or Project Manager
        """
        project = self.get_object()

        # Get the membership
        try:
            membership = ProjectMembers.objects.get(
                project=project, project_member_id=member_id
            )
        except ProjectMembers.DoesNotExist:
            return self._error(
                "MEMBER_NOT_FOUND",
                "Team member not found in this project",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Prevent project creator from being removed
        if membership.project_member == project.created_by:
            return self._error(
                "INVALID_OPERATION",
                "Cannot remove the project creator from the team",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: implement leave action
        # Prevent users from removing themselves (they should use leave action)
        if membership.project_member == request.user:
            return self._error(
                "INVALID_OPERATION",
                "Use the leave option to remove yourself from the project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        username = membership.project_member.username
        membership.delete()

        return self._success(
            message=f"{username} has been removed from the project team",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Successfully left the project"),
            400: OpenApiResponse(
                description="Bad Request - Cannot leave if you're the creator"
            ),
        },
        description="Leave a project team. Project creators cannot leave their own projects.",
    )
    @action(detail=True, methods=["post"], url_path="team/leave")
    def leave_project(self, request, pk=None):
        """
        Allow a user to leave a project team.
        Project creators cannot leave their own projects.
        """
        project = self.get_object()

        # Check if user is the project creator
        if project.created_by == request.user:
            return self._error(
                "INVALID_OPERATION",
                "Project creators cannot leave their own projects. Transfer ownership or delete the project instead.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Get the membership
        try:
            membership = ProjectMembers.objects.get(
                project=project, project_member=request.user
            )
            membership.delete()

            return self._success(
                message=f"You have successfully left {project.project_name}"
            )
        except ProjectMembers.DoesNotExist:
            return self._error(
                "NOT_A_MEMBER",
                "You are not a member of this project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = ExtendedUserSerializer
