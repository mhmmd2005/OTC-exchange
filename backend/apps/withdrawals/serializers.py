from rest_framework import serializers

from apps.assets.models import AssetNetwork

from .models import WithdrawalAddress
from .services.address_service import (
    WithdrawalAddressService,
)
from .validators.base import AddressValidationError


class WithdrawalAddressSerializer(
    serializers.ModelSerializer
):
    assetSymbol = serializers.CharField(
        source="network.asset.symbol",
        read_only=True,
    )

    assetNameFa = serializers.CharField(
        source="network.asset.name_fa",
        read_only=True,
    )

    assetNameEn = serializers.CharField(
        source="network.asset.name",
        read_only=True,
    )

    networkCode = serializers.CharField(
        source="network.code",
        read_only=True,
    )

    networkName = serializers.CharField(
        source="network.name",
        read_only=True,
    )

    networkDisplayName = serializers.CharField(
        source="network.display_name",
        read_only=True,
    )

    verificationMethod = serializers.CharField(
        source="verification_method",
        read_only=True,
    )

    isDefault = serializers.BooleanField(
        source="is_default",
        read_only=True,
    )

    confirmationRequestedAt = serializers.DateTimeField(
        source="confirmation_requested_at",
        read_only=True,
    )

    confirmedAt = serializers.DateTimeField(
        source="confirmed_at",
        read_only=True,
    )

    cooldownUntil = serializers.DateTimeField(
        source="cooldown_until",
        read_only=True,
    )

    activatedAt = serializers.DateTimeField(
        source="activated_at",
        read_only=True,
    )

    lastUsedAt = serializers.DateTimeField(
        source="last_used_at",
        read_only=True,
    )

    revokedAt = serializers.DateTimeField(
        source="revoked_at",
        read_only=True,
    )

    blockedReason = serializers.CharField(
        source="blocked_reason",
        read_only=True,
    )

    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    updatedAt = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

    class Meta:
        model = WithdrawalAddress
        fields = [
            "id",
            "assetSymbol",
            "assetNameFa",
            "assetNameEn",
            "networkCode",
            "networkName",
            "networkDisplayName",
            "address",
            "memo",
            "label",
            "status",
            "verificationMethod",
            "isDefault",
            "confirmationRequestedAt",
            "confirmedAt",
            "cooldownUntil",
            "activatedAt",
            "lastUsedAt",
            "revokedAt",
            "blockedReason",
            "createdAt",
            "updatedAt",
        ]


class WithdrawalAddressCreateSerializer(
    serializers.Serializer
):
    asset = serializers.CharField(
        max_length=16,
    )

    network = serializers.CharField(
        max_length=16,
    )

    address = serializers.CharField(
        max_length=255,
    )

    memo = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )

    label = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        asset_symbol = (
            attrs["asset"].strip().upper()
        )

        network_code = (
            attrs["network"].strip().upper()
        )

        address = (
            attrs["address"].strip()
        )

        memo = (
            attrs.get("memo", "").strip()
        )

        label = (
            attrs.get("label", "").strip()
        )

        if not asset_symbol:
            raise serializers.ValidationError({
                "asset": "ارز را انتخاب کنید."
            })

        if not network_code:
            raise serializers.ValidationError({
                "network": "شبکه را انتخاب کنید."
            })

        if not address:
            raise serializers.ValidationError({
                "address": "آدرس برداشت را وارد کنید."
            })

        try:
            network = (
                AssetNetwork.objects
                .select_related("asset")
                .get(
                    asset__symbol__iexact=asset_symbol,
                    asset__is_active=True,
                    code__iexact=network_code,
                )
            )
        except AssetNetwork.DoesNotExist:
            raise serializers.ValidationError({
                "network": (
                    "شبکه انتخاب‌شده برای این ارز معتبر نیست."
                )
            })

        if not network.asset.withdrawal_enabled:
            raise serializers.ValidationError({
                "asset": (
                    "برداشت این ارز در حال حاضر فعال نیست."
                )
            })

        if not network.withdrawal_enabled:
            raise serializers.ValidationError({
                "network": (
                    "برداشت روی این شبکه در حال حاضر فعال نیست."
                )
            })

        if network.status in {
            "disabled",
            "maintenance",
        }:
            raise serializers.ValidationError({
                "network": (
                    "این شبکه در حال حاضر در دسترس نیست."
                )
            })

        if network.memo_required and not memo:
            raise serializers.ValidationError({
                "memo": (
                    "برای این شبکه وارد کردن ممو یا تگ الزامی است."
                )
            })

        try:
            validation = (
                WithdrawalAddressService.validate(
                    network=network,
                    address=address,
                )
            )
        except AddressValidationError as exc:
            raise serializers.ValidationError({
                "address": str(exc)
            })

        if (
            WithdrawalAddress.objects.filter(
                user=self.context["request"].user,
                network=network,
                normalized_address=validation.normalized_address,
                memo=memo,
            ).exists()
        ):
            raise serializers.ValidationError({
                "address": (
                    "این آدرس قبلاً در فهرست شما ثبت شده است."
                )
            })

        attrs["asset"] = asset_symbol
        attrs["network"] = network_code
        attrs["address"] = address
        attrs["normalized_address"] = (
            validation.normalized_address
        )
        attrs["memo"] = memo
        attrs["label"] = label
        attrs["asset_network"] = network

        return attrs

    def create(self, validated_data):
        network = validated_data.pop(
            "asset_network"
        )

        validated_data.pop(
            "asset",
            None,
        )

        validated_data.pop(
            "network",
            None,
        )

        normalized_address = validated_data.pop(
            "normalized_address"
        )

        from django.utils import timezone

        return WithdrawalAddress.objects.create(
            user=self.context["request"].user,
            network=network,
            normalized_address=normalized_address,
            status=WithdrawalAddress.Status.PENDING_CONFIRMATION,
            verification_method=(
                WithdrawalAddress.VerificationMethod.SECURITY_CONFIRMATION
            ),
            confirmation_requested_at=timezone.now(),
            **validated_data,
        )


class WithdrawalAddressConfirmSerializer(
    serializers.Serializer
):
    challengeId = serializers.CharField(
        max_length=64,
    )

    otp = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    twoFactorCode = serializers.CharField(
        min_length=6,
        max_length=6,
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )

        challenge_id = (
            str(attrs["challengeId"])
            .translate(translation)
            .strip()
        )

        otp = (
            str(attrs["otp"])
            .translate(translation)
            .strip()
        )

        two_factor_code = (
            str(
                attrs.get(
                    "twoFactorCode",
                    "",
                )
            )
            .translate(translation)
            .strip()
        )

        if not challenge_id.isdigit():
            raise serializers.ValidationError({
                "challengeId": (
                    "شناسه درخواست تأیید معتبر نیست."
                )
            })

        if (
            not otp.isdigit()
            or len(otp) != 6
        ):
            raise serializers.ValidationError({
                "otp": (
                    "کد پیامکی باید ۶ رقمی باشد."
                )
            })

        if two_factor_code and (
            not two_factor_code.isdigit()
            or len(two_factor_code) != 6
        ):
            raise serializers.ValidationError({
                "twoFactorCode": (
                    "کد Authenticator باید ۶ رقمی باشد."
                )
            })

        attrs["challengeId"] = challenge_id
        attrs["otp"] = otp
        attrs["twoFactorCode"] = two_factor_code

        return attrs