from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Ticket
from .serializers import TicketSerializer


class TicketListAPIView(generics.ListAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [AllowAny]
