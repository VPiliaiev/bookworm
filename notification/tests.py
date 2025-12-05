from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from notification.views import send_telegram_message


User = get_user_model()


class NotificationBorrowingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )

        self.book = Book.objects.create(
            title="Test Book", author="Author", inventory=5, daily_fee=10
        )

        self.borrow_date = timezone.now().date()
        self.return_date = self.borrow_date + timedelta(days=5)

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=self.borrow_date,
            expected_return_date=self.return_date,
        )

    @patch("notification.views.requests.post")
    def test_notification_borrow_create(self, mock_post):
        send_telegram_message("123", f"Borrow created: {self.borrowing.id}")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        self.assertIn("Borrow created", kwargs["json"]["text"])

    @patch("notification.views.requests.post")
    def test_notification_payment_success(self, mock_post):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="http://stripe.test",
            session_id="session123",
            money_to_pay=50,
            type="payment",
            status="paid",
        )

        send_telegram_message("123", f"Payment success: {payment.id}")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        self.assertIn("Payment success", kwargs["json"]["text"])

    @patch("notification.views.requests.post")
    def test_notification_return_book(self, mock_post):
        self.borrowing.actual_return_date = timezone.now().date()
        self.borrowing.save()

        send_telegram_message("123", f"Book returned: {self.borrowing.id}")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        self.assertIn("Book returned", kwargs["json"]["text"])
