from rest_framework import serializers

from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    senderName = serializers.SerializerMethodField()
    body = serializers.CharField(source="message")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "sender",
            "senderName",
            "body",
            "createdAt",
        ]
        read_only_fields = fields

    def get_sender(self, obj):
        request = self.context.get("request")
        if request and obj.sender_id == request.user.id:
            return "user"
        return "support"

    def get_senderName(self, obj):
        return obj.sender.full_name or obj.sender.phone_number


class TicketSerializer(serializers.ModelSerializer):
    ticketNumber = serializers.SerializerMethodField()
    orderId = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticketNumber",
            "subject",
            "category",
            "status",
            "priority",
            "orderId",
            "createdAt",
            "updatedAt",
            "messages",
        ]
        read_only_fields = [
            "id",
            "ticketNumber",
            "status",
            "createdAt",
            "updatedAt",
            "messages",
        ]

    def get_ticketNumber(self, obj):
        return f"TK-{obj.id:05d}"

    def get_orderId(self, obj):
        return None


class CreateTicketSerializer(serializers.Serializer):
    subject = serializers.CharField(min_length=5, max_length=255)
    category = serializers.ChoiceField(
        choices=[choice[0] for choice in Ticket.CATEGORY_CHOICES]
    )
    body = serializers.CharField(min_length=10)
    orderId = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CreateTicketMessageSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=2)
