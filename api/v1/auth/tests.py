from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthLoginTests(APITestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username="seededuser",
            email="seeded@example.com",
            password="defaultPassword123",
        )
        self.inactive_user = User.objects.create_user(
            username="inactiveuser",
            email="inactive@example.com",
            password="defaultPassword123",
            is_active=False,
        )

    def test_login_accepts_email(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": self.active_user.email,
                "password": "defaultPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    def test_login_accepts_username(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": self.active_user.username,
                "password": "defaultPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    def test_login_rejects_inactive_user(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": self.inactive_user.email,
                "password": "defaultPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "AUTHENTICATION_FAILED")
