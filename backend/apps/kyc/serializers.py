from datetime import date

from rest_framework import serializers

from apps.accounts.serializers import BankAccountSerializer
from .models import KycApplication


def normalize_digits(value):
    return str(value).translate(str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    ))


def jalali_to_gregorian(year, month, day):
    year += 1595
    days = (
            -355668
            + 365 * year
            + (year // 33) * 8
            + ((year % 33 + 3) // 4)
            + day
    )
    days += (month - 1) * 31 if month < 7 else (month - 7) * 30 + 186

    gy = 400 * (days // 146097)
    days %= 146097

    if days > 36524:
        gy += 100 * ((days - 1) // 36524)
        days = (days - 1) % 36524
        if days >= 365:
            days += 1

    gy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365

    gd = days + 1
    leap = gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0)
    month_days = [
        31, 29 if leap else 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31,
    ]

    gm = 1
    while gd > month_days[gm - 1]:
        gd -= month_days[gm - 1]
        gm += 1

    return date(gy, gm, gd)


def parse_birth_date(value):
    value = normalize_digits(value).strip().replace("-", "/")
    parts = value.split("/")

    if len(parts) != 3:
        raise serializers.ValidationError(
            "تاریخ تولد را به صورت ۱۳۷۲/۰۸/۱۹ وارد کنید."
        )

    try:
        year, month, day = map(int, parts)
    except ValueError as exc:
        raise serializers.ValidationError(
            "تاریخ تولد معتبر نیست."
        ) from exc

    if not (
            1200 <= year <= 1600
            and 1 <= month <= 12
            and 1 <= day <= 31
    ):
        raise serializers.ValidationError(
            "تاریخ تولد معتبر نیست."
        )

    try:
        result = jalali_to_gregorian(year, month, day)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError(
            "تاریخ تولد معتبر نیست."
        ) from exc

    if result > date.today():
        raise serializers.ValidationError(
            "تاریخ تولد نمی‌تواند در آینده باشد."
        )

    return result


class KycApplicationSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    can_edit_basic_info = serializers.SerializerMethodField()
    can_edit_identity = serializers.SerializerMethodField()

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
            "basic_info_status",
            "basic_info_submitted_at",
            "basic_info_reviewed_at",
            "basic_info_rejection_reason",
            "can_edit_basic_info",
            "identity_status",
            "identity_submitted_at",
            "identity_reviewed_at",
            "identity_rejection_reason",
            "can_edit_identity",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "phone_number",
            "status",
            "status_label",
            "basic_info_status",
            "basic_info_submitted_at",
            "basic_info_reviewed_at",
            "basic_info_rejection_reason",
            "can_edit_basic_info",
            "identity_status",
            "identity_submitted_at",
            "identity_reviewed_at",
            "identity_rejection_reason",
            "can_edit_identity",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]

    def get_phone_number(self, obj):
        return obj.user.phone_number

    def get_status_label(self, obj):
        return obj.get_status_display()

    def get_can_edit_basic_info(self, obj):
        return obj.can_edit_basic_info

    def get_can_edit_identity(self, obj):
        return obj.can_edit_identity


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
            "identity_document",
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
        accounts = obj.user.bank_accounts.select_related("bank").all()
        return BankAccountSerializer(accounts, many=True).data


class BasicInfoSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", max_length=64)
    lastName = serializers.CharField(source="last_name", max_length=96)
    nationalId = serializers.CharField(source="national_id", max_length=10)
    birthDate = serializers.CharField(write_only=True)

    class Meta:
        model = KycApplication
        fields = [
            "firstName",
            "lastName",
            "nationalId",
            "birthDate",
        ]

    def validate_firstName(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("نام را وارد کنید.")
        return value

    def validate_lastName(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "نام خانوادگی را وارد کنید."
            )
        return value

    def validate_nationalId(self, value):
        value = normalize_digits(value).strip()

        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                "کد ملی باید ۱۰ رقم باشد."
            )

        if len(set(value)) == 1:
            raise serializers.ValidationError(
                "کد ملی معتبر نیست."
            )

        digits = [int(item) for item in value]
        total = sum(
            digits[index] * (10 - index)
            for index in range(9)
        )
        remainder = total % 11
        expected = remainder if remainder < 2 else 11 - remainder

        if digits[-1] != expected:
            raise serializers.ValidationError(
                "کد ملی معتبر نیست."
            )

        return value

    def validate_birthDate(self, value):
        return parse_birth_date(value)

    def validate(self, attrs):
        attrs["birth_date"] = attrs.pop("birthDate")
        return attrs


class IdentityDocumentSerializer(serializers.Serializer):
    document = serializers.FileField()

    def validate_document(self, value):
        if value.content_type not in {
            "image/jpeg",
            "image/png",
            "application/pdf",
        }:
            raise serializers.ValidationError(
                "فرمت مدرک باید JPG، PNG یا PDF باشد."
            )

        if not value.size:
            raise serializers.ValidationError(
                "فایل انتخاب‌شده خالی است."
            )

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "حجم مدرک نباید بیشتر از ۵ مگابایت باشد."
            )

        return value


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
