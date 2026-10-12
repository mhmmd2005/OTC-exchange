from django.urls import re_path

from .consumers import SupportTicketConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/support/tickets/(?P<ticket_id>\d+)/$",
        SupportTicketConsumer.as_asgi(),
    ),
]