from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

from book.models import Book

BOOK_LIST_URL = reverse("book:book-list")


def book_detail_url(book_id):
    return reverse("book:book-detail", args=[book_id])


def sample_user(**params):
    defaults = {
        "email": "user@test.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def sample_admin_user(**params):
    defaults = {
        "email": "admin@test.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(params)
    return get_user_model().objects.create_superuser(**defaults)


def sample_book(**params):
    defaults = {
        "title": "Default Book",
        "author": "Unknown",
        "cover": "hard",
        "inventory": 10,
        "daily_fee": "1.99",
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BOOK_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_book_unauthenticated(self):
        payload = {
            "title": "Test Book",
            "author": "Someone",
            "cover": "hard",
            "inventory": 5,
            "daily_fee": "1.99",
        }
        res = self.client.post(BOOK_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_book_list(self):
        sample_book()
        sample_book(title="Another Book")

        res = self.client.get(BOOK_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)

    def test_retrieve_book_detail(self):
        book = sample_book(title="Some book")
        url = book_detail_url(book.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], book.id)
        self.assertEqual(res.data["title"], book.title)

    def test_user_cannot_create_book(self):
        payload = {
            "title": "New Book",
            "author": "Author",
            "cover": "hard",
            "inventory": 5,
            "daily_fee": "1.99",
        }

        res = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Book.objects.count(), 0)

    def test_user_cannot_update_book(self):
        book = sample_book()
        url = book_detail_url(book.id)

        res = self.client.patch(url, {"title": "Updated Title"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        book.refresh_from_db()
        self.assertNotEqual(book.title, "Updated Title")

    def test_user_cannot_delete_book(self):
        book = sample_book()
        url = book_detail_url(book.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(id=book.id).exists())


class AdminBookApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin_user = sample_admin_user()
        self.client.force_authenticate(self.admin_user)

    def test_admin_can_create_book(self):
        payload = {
            "title": "Admin Book",
            "author": "Admin Author",
            "cover": "soft",
            "inventory": 10,
            "daily_fee": "2.50",
        }
        res = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Book.objects.first().title, payload["title"])

    def test_admin_can_retrieve_book_list(self):
        sample_book()
        sample_book(title="Another Book")

        res = self.client.get(BOOK_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)

    def test_admin_can_retrieve_book_detail(self):
        book = sample_book()
        url = book_detail_url(book.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], book.id)
        self.assertEqual(res.data["title"], book.title)

    def test_admin_can_update_book(self):
        book = sample_book()
        url = book_detail_url(book.id)

        payload = {"title": "Updated Title", "inventory": 20}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.title, payload["title"])
        self.assertEqual(book.inventory, payload["inventory"])

    def test_admin_can_delete_book(self):
        book = sample_book()
        url = book_detail_url(book.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
