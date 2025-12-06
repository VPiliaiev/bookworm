from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingCreateSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)
from notification.views import send_telegram_message
from payment.views import create_stripe_checkout
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


class BorrowingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 10


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user").order_by("-borrow_date")
    permission_classes = [IsAuthenticated]
    pagination_class = BorrowingPagination

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingDetailSerializer

    @staticmethod
    def _str_to_bool(param):
        if param is None:
            return None
        return param.lower() in ("true", "1")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_id",
                type=int,
                description="Filter by user id admin only",
                required=False,
            ),
            OpenApiParameter(
                "is_active",
                type=bool,
                description="Filter by active borrowings",
                required=False,
            ),
        ],
        responses=BorrowingListSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        is_active = self._str_to_bool(self.request.query_params.get("is_active"))

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active is not None:
            queryset = queryset.filter(actual_return_date__isnull=is_active)

        return queryset

    @extend_schema(
        summary="Create borrowing",
        description=(
            "Creates a new borrowing, decreases book inventory, creates a Stripe "
            "checkout session and send a Telegram notification."
            "Returns: `borrowing_id` and `checkout_url`."
        ),
        request=BorrowingCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="Borrowing successfully created",
                examples={
                    "example": {
                        "borrowing_id": 12,
                        "checkout_url": "https://checkout.stripe.com/pay/test123",
                    }
                },
            ),
            400: OpenApiResponse(description="Validation error"),
            409: OpenApiResponse(description="Book out of stock"),
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = serializer.validated_data["book"]

        with transaction.atomic():
            borrowing = serializer.save(
                user=request.user,
                borrow_date=timezone.now().date(),
            )
            book.inventory -= 1
            book.save()

        checkout_url = create_stripe_checkout(borrowing)

        days = (borrowing.expected_return_date - borrowing.borrow_date).days
        amount = borrowing.book.daily_fee * days

        send_telegram_message(
            settings.TELEGRAM_ADMIN_CHAT_ID,
            (
                f"<b>New Borrowing Created</b>\n\n"
                f"User: {request.user.email}\n"
                f"Book: {borrowing.book.title}\n"
                f"Borrow date: {borrowing.borrow_date}\n"
                f"Return date: {borrowing.expected_return_date}\n"
                f"Amount to pay: {amount}$"
            ),
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "borrowing_id": borrowing.id,
                "checkout_url": checkout_url,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @extend_schema(
        description="Return a borrowed book. Send Telegram notification to admin.",
        responses={
            200: {"status": "book returned"},
            400: {"detail": "Book already returned."},
        },
    )
    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "Book already returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            Borrowing.objects.filter(pk=borrowing.pk).update(
                actual_return_date=borrowing.actual_return_date
            )
            borrowing.book.inventory += 1
            borrowing.book.save()

        send_telegram_message(
            settings.TELEGRAM_ADMIN_CHAT_ID,
            f"User {borrowing.user} return the book: {borrowing.book.title}",
        )
        return Response({"status": "book returned"})
