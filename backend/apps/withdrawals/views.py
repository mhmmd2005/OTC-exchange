from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import WithdrawalAddress
from .serializers import (
    WithdrawalAddressConfirmSerializer,
    WithdrawalAddressCreateSerializer,
    WithdrawalAddressSerializer,
)
from .services.confirmation_service import (
    WithdrawalAddressConfirmationService,
)


class WithdrawalAddressListCreateAPIView(
    generics.ListCreateAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return (
            WithdrawalAddress.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "network",
                "network__asset",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WithdrawalAddressCreateSerializer

        return WithdrawalAddressSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not request.user.is_phone_verified:
            return Response(
                {
                    "detail": (
                        "برای افزودن آدرس برداشت ابتدا شماره موبایل خود را تأیید کنید."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            instance = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "این آدرس قبلاً برای حساب شما ثبت شده است."
                    ),
                    "fields": {
                        "address": (
                            "این آدرس قبلاً ثبت شده است."
                        )
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        confirmation = (
            WithdrawalAddressConfirmationService.request_confirmation(
                address=instance,
                user=request.user,
                request_ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )
        )

        output_serializer = (
            WithdrawalAddressSerializer(
                instance
            )
        )

        return Response(
            {
                "address": output_serializer.data,
                "confirmation": confirmation,
            },
            status=status.HTTP_201_CREATED,
        )


class WithdrawalAddressConfirmationAPIView(
    generics.GenericAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    serializer_class = (
        WithdrawalAddressConfirmSerializer
    )

    def post(self, request, pk):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            address = (
                WithdrawalAddressConfirmationService.confirm(
                    address_id=pk,
                    user=request.user,
                    challenge_id=(
                        serializer.validated_data[
                            "challengeId"
                        ]
                    ),
                    otp=(
                        serializer.validated_data[
                            "otp"
                        ]
                    ),
                    two_factor_code=(
                        serializer.validated_data.get(
                            "twoFactorCode",
                            "",
                        )
                    ),
                    request_ip=request.META.get(
                        "REMOTE_ADDR"
                    ),
                )
            )
        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(
            WithdrawalAddressSerializer(
                address
            ).data,
            status=status.HTTP_200_OK,
        )


class WithdrawalAddressResendConfirmationAPIView(
    generics.GenericAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):
        try:
            address = (
                WithdrawalAddress.objects
                .filter(
                    id=pk,
                    user=request.user,
                )
                .first()
            )

            if not address:
                return Response(
                    {
                        "detail": (
                            "آدرس برداشت پیدا نشد."
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            confirmation = (
                WithdrawalAddressConfirmationService.request_confirmation(
                    address=address,
                    user=request.user,
                    request_ip=request.META.get(
                        "REMOTE_ADDR"
                    ),
                    user_agent=request.META.get(
                        "HTTP_USER_AGENT",
                        "",
                    ),
                )
            )

            return Response(
                {
                    "address": (
                        WithdrawalAddressSerializer(
                            address
                        ).data
                    ),
                    "confirmation": confirmation,
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )


class WithdrawalAddressDetailAPIView(
    generics.RetrieveDestroyAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    serializer_class = WithdrawalAddressSerializer

    def get_queryset(self):
        return (
            WithdrawalAddress.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "network",
                "network__asset",
            )
        )

    def retrieve(
            self,
            request,
            *args,
            **kwargs,
    ):
        instance = self.get_object()

        if instance.status == (
                WithdrawalAddress.Status.COOLING_DOWN
        ):
            instance = (
                    WithdrawalAddressConfirmationService.activate_if_ready(
                        address_id=instance.id,
                        user=request.user,
                        request_ip=request.META.get(
                            "REMOTE_ADDR"
                        ),
                    )
                    or instance
            )

        return Response(
            self.get_serializer(
                instance
            ).data,
            status=status.HTTP_200_OK,
        )

    def destroy(
            self,
            request,
            *args,
            **kwargs,
    ):
        instance = self.get_object()

        if instance.status == (
                WithdrawalAddress.Status.BLOCKED
        ):
            return Response(
                {
                    "detail": (
                        "آدرس مسدودشده را نمی‌توان حذف کرد."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if instance.status == (
                WithdrawalAddress.Status.PENDING_CONFIRMATION
        ):
            instance.delete()

            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

        instance.status = (
            WithdrawalAddress.Status.REVOKED
        )

        instance.is_default = False
        instance.revoked_at = timezone.now()

        instance.save(
            update_fields=[
                "status",
                "is_default",
                "revoked_at",
                "updated_at",
            ]
        )

        from apps.security.models import SecurityEvent

        SecurityEvent.objects.create(
            user=request.user,
            event_type="withdrawal_addr_revoked",
            description=(
                "آدرس برداشت توسط کاربر لغو شد."
            ),
            ip_address=request.META.get(
                "REMOTE_ADDR"
            ),
        )

        return Response(
            {
                "detail": (
                    "آدرس برداشت با موفقیت غیرفعال شد."
                )
            },
            status=status.HTTP_200_OK,
        )


class WithdrawalAddressSetDefaultAPIView(
    generics.GenericAPIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):
        try:
            address = (
                WithdrawalAddressConfirmationService.activate_if_ready(
                    address_id=pk,
                    user=request.user,
                    request_ip=request.META.get(
                        "REMOTE_ADDR"
                    ),
                )
            )

            if not address:
                return Response(
                    {
                        "detail": (
                            "آدرس برداشت پیدا نشد."
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if address.status != (
                    WithdrawalAddress.Status.ACTIVE
            ):
                return Response(
                    {
                        "detail": (
                            "فقط آدرس فعال می‌تواند به‌عنوان آدرس پیش‌فرض انتخاب شود."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            with transaction.atomic():
                (
                    WithdrawalAddress.objects
                    .filter(
                        user=request.user
                    )
                    .update(
                        is_default=False
                    )
                )

                address.is_default = True

                address.save(
                    update_fields=[
                        "is_default",
                        "updated_at",
                    ]
                )

            from apps.security.models import SecurityEvent

            SecurityEvent.objects.create(
                user=request.user,
                event_type="withdrawal_addr_default",
                description=(
                    "آدرس پیش‌فرض برداشت تغییر کرد."
                ),
                ip_address=request.META.get(
                    "REMOTE_ADDR"
                ),
            )

            return Response(
                WithdrawalAddressSerializer(
                    address
                ).data,
                status=status.HTTP_200_OK,
            )

        except ValidationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
