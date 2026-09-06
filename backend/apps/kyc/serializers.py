from rest_framework import serializers

from .models import KycApplication


class KycApplicationSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()

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
            "identity_document",
            "status",
            "status_label",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "can_edit",
            "can_submit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "phone_number",
            "status",
            "status_label",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "can_edit",
            "can_submit",
            "created_at",
            "updated_at",
        ]

    def get_phone_number(self, obj):
        return obj.user.phone_number

    def get_status_label(self, obj):
        return obj.get_status_display()

    def get_can_edit(self, obj):
        return obj.can_edit

    def get_can_submit(self, obj):
        return obj.can_submit

    def validate_identity_document(self, value):
        if value:
            allowed_types = ["image/jpeg", "image/png", "application/pdf"]
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("فرمت مدرک باید JPG، PNG یا PDF باشد.")

            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("حجم فایل نباید بیشتر از 5 مگابایت باشد.")

        return value
