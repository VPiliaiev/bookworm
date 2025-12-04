import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from borrowing.models import Borrowing
from payment.models import Payment
from django.shortcuts import redirect


def create_stripe_checkout(borrowing: Borrowing) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    days = (borrowing.expected_return_date - borrowing.borrow_date).days
    money_to_pay = borrowing.book.daily_fee * days

    payment = Payment.objects.create(
        borrowing=borrowing,
        money_to_pay=money_to_pay,
        status=Payment.StatusChoices.PENDING,
    )

    domain_url = "http://localhost:8000/"

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing {borrowing.id} - {borrowing.book.title}"
                    },
                    "unit_amount": int(payment.money_to_pay * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=domain_url + "payment/success/?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=domain_url + "payment/cancelled/",
    )

    payment.session_id = checkout_session.id
    payment.session_url = checkout_session.url
    payment.save()

    return payment.session_url


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment = Payment.objects.filter(session_id=session["id"]).first()
        if payment:
            payment.status = Payment.StatusChoices.PAID
            payment.save()

    return HttpResponse(status=200)


def payment_success(request):
    return redirect("/api/borrowings/")


def payment_cancel(request):
    return redirect("/api/borrowings/")
