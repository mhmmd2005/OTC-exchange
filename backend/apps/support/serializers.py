from rest_framework import serializers

from .models import Ticket, TicketMessage


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "subject",
            "category",
            "status",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ["id", "ticket", "sender", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
