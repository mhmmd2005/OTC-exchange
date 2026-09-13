from django.urls import path

from .views import OTCOrderCreateAPIView, OTCQuoteCreateAPIView, OTCQuoteDetailAPIView

urlpatterns = [
    path("quotes", OTCQuoteCreateAPIView.as_view(), name="otc-quote-create"),
    path("quotes/<int:id>", OTCQuoteDetailAPIView.as_view(), name="otc-quote-detail"),
    path("orders", OTCOrderCreateAPIView.as_view(), name="otc-order-create"),
]
