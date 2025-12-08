from django.db import models

from borrowing.models import Borrowing


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "pending"
        PAID = "paid"

    class TypeChoice(models.TextChoices):
        PAYMENT = "payment"
        FINE = "fine"

    status = models.CharField(
        max_length=64, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )
    type = models.CharField(
        max_length=64, choices=TypeChoice.choices, default=TypeChoice.PAYMENT
    )
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=1000, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
