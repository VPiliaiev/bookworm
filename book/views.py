from rest_framework import viewsets
from book.models import Book
from book.permissions import IsAdminOrAuthReadOnly
from book.serializers import BookListSerializer, BookDetailSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    permission_classes = [IsAdminOrAuthReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        return BookDetailSerializer
