from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import OTCQuote
from .serializers import OTCQuoteSerializer


class OTCQuoteListAPIView(generics.ListAPIView):
    queryset = OTCQuote.objects.all()
    serializer_class = OTCQuoteSerializer
    permission_classes = [AllowAny]
