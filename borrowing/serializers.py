from rest_framework import serializers
from django.utils import timezone
from borrowing.models import Borrowing
from book.serializers import BookListSerializer, BookDetailSerializer
from user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")


class BorrowingCreateSerializer(serializers.ModelSerializer):
    expected_return_date = serializers.DateField(required=True)

    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")
        read_only_fields = ("id",)

    def validate(self, attrs):
        book = attrs.get("book")
        expected_return_date = attrs.get("expected_return_date")
        borrow_date = timezone.now().date()

        Borrowing.validate_inventory(book, serializers.ValidationError)
        Borrowing.validate_expected_return(
            borrow_date,
            expected_return_date,
            serializers.ValidationError,
        )
        return attrs


class BorrowingListSerializer(serializers.ModelSerializer):
    book = BookListSerializer()
    user = UserSerializer()
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
            "book",
            "user",
        )


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookDetailSerializer()
    user = UserSerializer()
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
            "book",
            "user",
        )
