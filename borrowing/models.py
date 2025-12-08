from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="book_borrowings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_borrowings",
    )

    def __str__(self):
        return f"Borrowed {self.book.title} by {self.user.email} on {self.borrow_date}"

    @property
    def is_active(self):
        return self.actual_return_date is None

    @staticmethod
    def validate_expected_return(borrow_date, expected_return, error_to_raise):
        if expected_return is None:
            raise error_to_raise({"expected_return_date": "This field is required."})
        if expected_return <= borrow_date:
            raise error_to_raise(
                {
                    "expected_return_date": "Expected return date must be after borrow date."
                }
            )

    @staticmethod
    def validate_inventory(book, error_to_raise):
        if book.inventory < 1:
            raise error_to_raise({"book": "No copies available."})

    def clean(self):
        super().clean()
        Borrowing.validate_inventory(self.book, ValidationError)
        Borrowing.validate_expected_return(
            self.borrow_date, self.expected_return_date, ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
