from django.urls import path
from payment.views import (
    create_stripe_checkout,
    stripe_webhook,
    payment_success,
    payment_cancel,
)

urlpatterns = [
    path("create-checkout/<int:borrowing_id>/", create_stripe_checkout),
    path("webhook/", stripe_webhook),
    path("success/", payment_success),
    path("cancel/", payment_cancel),
]
