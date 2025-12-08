from django.test import TestCase, Client
from unittest.mock import patch, MagicMock

from rest_framework.utils import json
from stripe import SignatureVerificationError

from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from django.contrib.auth import get_user_model

from payment.views import create_stripe_checkout

User = get_user_model()


class PaymentCreateStripeSessionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123"
        )

        self.book = Book.objects.create(title="TestBook", daily_fee=1, inventory=10)

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date="2024-01-01",
            expected_return_date="2024-01-05",
        )

    @patch("payment.views.stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "ses_123"
        mock_session.url = "https://stripe.test/checkout/sess_123"

        mock_create.return_value = mock_session

        redirect_url = create_stripe_checkout(self.borrowing)

        payment = Payment.objects.get(borrowing=self.borrowing)

        self.assertEqual(payment.session_id, "ses_123")
        self.assertEqual(payment.session_url, "https://stripe.test/checkout/sess_123")
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)

        self.assertEqual(redirect_url, payment.session_url)

        mock_create.assert_called_once()


class StripeWebhookTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123"
        )

        self.book = Book.objects.create(title="Book", daily_fee=1, inventory=10)

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date="2024-01-01",
            expected_return_date="2024-01-05",
        )

        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            money_to_pay=10,
            status=Payment.StatusChoices.PENDING,
            session_id="sess_123",
        )

    @patch("payment.views.stripe.Webhook.construct_event")
    def test_webhook_marks_payment_as_paid(self, mock_event):
        mock_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "sess_123",
                }
            },
        }

        response = self.client.post(
            "/payment/webhook/",
            data=json.dumps({"id": "sess_123"}),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test_sig",
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)

    @patch("payment.views.stripe.Webhook.construct_event")
    def test_webhook_invalid_signature_returns_400(self, mock_event):
        mock_event.side_effect = SignatureVerificationError("Bad signature", "payload")

        response = self.client.post(
            "/payment/webhook/",
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="bad",
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)


class PaymentRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123"
        )
        self.client.force_login(self.user)

    def test_payment_success_redirects_to_borrowings(self):
        response = self.client.get("/payment/success/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/api/borrowings/")

    def test_payment_cancel_redirects_to_borrowings(self):
        response = self.client.get("/payment/cancel/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/api/borrowings/")
