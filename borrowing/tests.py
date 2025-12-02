from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from borrowing.models import Borrowing
from book.models import Book
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


BORROWING_LIST_URL = reverse("borrowing:borrowing-list")


class BorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@example.com", password="pass")
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="pass"
        )
        self.book = Book.objects.create(
            title="Test Book", author="Author", inventory=3, daily_fee=10
        )

    def test_unauthenticated_user_cannot_borrow(self):
        data = {
            "book": self.book.id,
            "expected_return_date": (
                timezone.now().date() + timedelta(days=7)
            ).isoformat(),
        }
        res = self.client.post(BORROWING_LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_borrow_book(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "book": self.book.id,
            "expected_return_date": (
                timezone.now().date() + timedelta(days=7)
            ).isoformat(),
        }
        res = self.client.post(BORROWING_LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_authenticated_user_can_return_book(self):
        borrow_date = timezone.now().date()
        borrowing = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
        )
        borrowing.save()

        self.book.inventory -= 1
        self.book.save()

        self.client.force_authenticate(user=self.user)
        return_url = reverse(
            "borrowing:borrowing-return-book", kwargs={"pk": borrowing.id}
        )
        res = self.client.post(return_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)

    def test_user_can_see_only_own_borrowings(self):
        borrow_date = timezone.now().date()

        other_user = User.objects.create_user(
            email="other@example.com", password="pass"
        )
        borrowing_other = Borrowing(
            user=other_user,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
        )
        borrowing_other.save()

        borrowing_self = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
        )
        borrowing_self.save()

        self.client.force_authenticate(user=self.user)
        res = self.client.get(BORROWING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["user"]["id"], self.user.id)

    def test_admin_see_all_borrowings(self):
        borrow_date = timezone.now().date()

        borrowing_user = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
        )
        borrowing_user.save()

        borrowing_admin = Borrowing(
            user=self.admin,
            book=self.book,
            borrow_date=borrow_date,
            expected_return_date=borrow_date + timedelta(days=7),
        )
        borrowing_admin.save()

        self.client.force_authenticate(user=self.admin)
        res = self.client.get(BORROWING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)
