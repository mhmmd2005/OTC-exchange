from django.urls import path

from .views import OTCQuoteListAPIView

urlpatterns = [
    path("", OTCQuoteListAPIView.as_view(), name="otc-quote-list"),
]
