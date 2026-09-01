from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionListAPIView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]
