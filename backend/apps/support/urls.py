from django.urls import path

from .views import (
    FAQListAPIView,
    TicketCloseAPIView,
    TicketDetailAPIView,
    TicketListCreateAPIView,
    TicketMessageCreateAPIView,
)

urlpatterns = [
    path(
        "faqs",
        FAQListAPIView.as_view(),
        name="faq-list",
    ),
    path(
        "tickets",
        TicketListCreateAPIView.as_view(),
        name="ticket-list-create",
    ),
    path(
        "tickets/<int:pk>",
        TicketDetailAPIView.as_view(),
        name="ticket-detail",
    ),
    path(
        "tickets/<int:pk>/messages",
        TicketMessageCreateAPIView.as_view(),
        name="ticket-message-create",
    ),
    path(
        "tickets/<int:pk>/close",
        TicketCloseAPIView.as_view(),
        name="ticket-close",
    ),
]