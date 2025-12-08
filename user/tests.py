from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
ME_URL = reverse("user:manage_user")


class UserApiTests(APITestCase):
    def test_create_user_success(self):
        payload = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_token_for_user(self):
        payload = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }
        get_user_model().objects.create_user(**payload)
        res = self.client.post(
            TOKEN_URL, {"email": payload["email"], "password": payload["password"]}
        )
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_user_profile_unauthorized(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
