from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from projects.models import ProjectMembers, ProjectsModel


class TeamUserAccessTests(APITestCase):
    @staticmethod
    def _extract_user_rows(response_data):
        if isinstance(response_data, dict) and "results" in response_data:
            return response_data["results"]
        return response_data

    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.pm_group, _ = Group.objects.get_or_create(name="Project Manager")
        self.dev_group, _ = Group.objects.get_or_create(name="Developer")

        self.admin_user = User.objects.create_user(
            username="admin_access",
            email="admin-access@example.com",
            password="defaultPassword123",
            is_staff=True,
        )
        self.admin_user.groups.add(self.admin_group)

        self.pm_user = User.objects.create_user(
            username="pm_access",
            email="pm-access@example.com",
            password="defaultPassword123",
        )
        self.pm_user.groups.add(self.pm_group)

        self.dev_user = User.objects.create_user(
            username="dev_access",
            email="dev-access@example.com",
            password="defaultPassword123",
        )
        self.dev_user.groups.add(self.dev_group)

        self.team_member = User.objects.create_user(
            username="team_member",
            email="team-member@example.com",
            password="defaultPassword123",
        )
        self.external_member = User.objects.create_user(
            username="external_member",
            email="external-member@example.com",
            password="defaultPassword123",
        )

        today = timezone.now().date()
        self.pm_project = ProjectsModel.objects.create(
            project_name="PM Team Project",
            description="Scoped project",
            start_date=today,
            end_date=today + timedelta(days=14),
            status="ACTIVE",
            priority="MEDIUM",
            created_by=self.admin_user,
        )

        self.external_project = ProjectsModel.objects.create(
            project_name="External Team Project",
            description="Outside PM scope",
            start_date=today,
            end_date=today + timedelta(days=14),
            status="ACTIVE",
            priority="MEDIUM",
            created_by=self.admin_user,
        )

        ProjectMembers.objects.create(
            project=self.pm_project,
            project_member=self.pm_user,
            role_in_project="Project Manager",
        )
        ProjectMembers.objects.create(
            project=self.pm_project,
            project_member=self.team_member,
            role_in_project="Developer",
        )
        ProjectMembers.objects.create(
            project=self.external_project,
            project_member=self.external_member,
            role_in_project="Developer",
        )

    def test_admin_can_view_available_teams(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/v1/accounts/team/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {
            user["username"] for user in self._extract_user_rows(response.data)
        }
        self.assertIn("team_member", usernames)
        self.assertIn("external_member", usernames)

    def test_project_manager_can_view_only_their_available_teams(self):
        self.client.force_authenticate(user=self.pm_user)
        response = self.client.get("/api/v1/accounts/team/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {
            user["username"] for user in self._extract_user_rows(response.data)
        }
        self.assertIn("team_member", usernames)
        self.assertNotIn("external_member", usernames)

    def test_non_admin_non_pm_cannot_view_available_teams(self):
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get("/api/v1/accounts/team/users/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "FORBIDDEN")
