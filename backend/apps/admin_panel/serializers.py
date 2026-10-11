from rest_framework import serializers
from apps.support.models import Ticket, TicketMessage
from apps.accounts.serializers import BankAccountSerializer
from apps.kyc.models import KycApplication

from .models import AdminUser


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class AdminRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        write_only=True,
    )


class AdminLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        write_only=True,
    )


class AdminIdentitySerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(
        source="full_name",
        read_only=True,
    )

    accountType = serializers.SerializerMethodField()

    class Meta:
        model = AdminUser
        fields = [
            "id",
            "email",
            "fullName",
            "role",
            "accountType",
        ]
        read_only_fields = fields

    def get_accountType(self, obj):
        return "admin"


class AdminKycApplicationSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    can_edit_basic_info = serializers.SerializerMethodField()
    can_edit_identity = serializers.SerializerMethodField()
    bank_accounts = serializers.SerializerMethodField()

    class Meta:
        model = KycApplication
        fields = [
            "id",
            "first_name",
            "last_name",
            "national_id",
            "birth_date",
            "phone_number",
            "email",
            "identity_document_front",
"identity_document_back",
            "status",
            "status_label",

            "basic_info_status",
            "basic_info_submitted_at",
            "basic_info_reviewed_at",
            "basic_info_reviewed_by",
            "basic_info_rejection_reason",
            "can_edit_basic_info",

            "identity_status",
            "identity_submitted_at",
            "identity_reviewed_at",
            "identity_reviewed_by",
            "identity_rejection_reason",
            "can_edit_identity",

            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",

            "bank_accounts",

            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_phone_number(self, obj):
        return obj.user.phone_number

    def get_status_label(self, obj):
        return obj.get_status_display()

    def get_can_edit_basic_info(self, obj):
        return obj.can_edit_basic_info

    def get_can_edit_identity(self, obj):
        return obj.can_edit_identity

    def get_bank_accounts(self, obj):
        accounts = (
            obj.user.bank_accounts
            .select_related("bank")
            .all()
        )

        return BankAccountSerializer(
            accounts,
            many=True,
        ).data


class KycRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
    )

    def validate_reason(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "دلیل رد کردن را وارد کنید."
            )

        return value



class AdminTicketMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    senderName = serializers.SerializerMethodField()
    body = serializers.CharField(source="message", read_only=True)
    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

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
        return "support" if obj.admin_sender_id else "user"

    def get_senderName(self, obj):
        if obj.admin_sender_id:
            admin = obj.admin_sender
            return admin.full_name or admin.email

        if obj.sender_id:
            user = obj.sender
            return user.full_name or user.phone_number

        return "—"


class AdminTicketListSerializer(serializers.ModelSerializer):
    ticketNumber = serializers.SerializerMethodField()
    userName = serializers.SerializerMethodField()
    userPhone = serializers.CharField(
        source="user.phone_number",
        read_only=True,
    )
    userEmail = serializers.EmailField(
        source="user.email",
        read_only=True,
        allow_null=True,
    )
    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )
    updatedAt = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )
    messageCount = serializers.IntegerField(
        source="message_count",
        read_only=True,
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticketNumber",
            "subject",
            "category",
            "status",
            "priority",
            "userName",
            "userPhone",
            "userEmail",
            "createdAt",
            "updatedAt",
            "messageCount",
        ]
        read_only_fields = fields

    def get_ticketNumber(self, obj):
        return f"TK-{obj.id:05d}"

    def get_userName(self, obj):
        return obj.user.full_name or obj.user.phone_number


class AdminTicketDetailSerializer(AdminTicketListSerializer):
    messages = AdminTicketMessageSerializer(
        many=True,
        read_only=True,
    )

    class Meta(AdminTicketListSerializer.Meta):
        fields = AdminTicketListSerializer.Meta.fields + [
            "messages",
        ]
        read_only_fields = fields


class AdminTicketReplySerializer(serializers.Serializer):
    body = serializers.CharField(
        min_length=2,
        max_length=10000,
        trim_whitespace=True,
    )

    def validate_body(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "متن پاسخ را وارد کنید."
            )

        return value


class AdminTicketStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Ticket.STATUS_CHOICES,
    )