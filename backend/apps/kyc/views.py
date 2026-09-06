from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import KycApplication
from .serializers import KycApplicationSerializer

User = get_user_model()


class GetOrCreateKycAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, created = KycApplication.objects.get_or_create(user=request.user)
        serializer = KycApplicationSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitKycAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        kyc, created = KycApplication.objects.get_or_create(user=request.user)

        if not kyc.can_submit:
            return Response(
                {"detail": f"Cannot submit KYC with status '{kyc.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = KycApplicationSerializer(kyc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        kyc.submit()
        updated_serializer = KycApplicationSerializer(kyc)
        return Response(updated_serializer.data, status=status.HTTP_200_OK)


class UpdateKycAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request):
        kyc, created = KycApplication.objects.get_or_create(user=request.user)

        if not kyc.can_edit:
            return Response(
                {"detail": f"Cannot edit KYC with status '{kyc.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = KycApplicationSerializer(kyc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class KycStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, created = KycApplication.objects.get_or_create(user=request.user)
        serializer = KycApplicationSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitKycAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        kyc, created = KycApplication.objects.get_or_create(user=request.user)

        if not kyc.can_submit:
            return Response(
                {"detail": "در وضعیت فعلی امکان ثبت مجدد درخواست وجود ندارد."},
                status=400,
            )

        serializer = KycApplicationSerializer(
            kyc,
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        kyc.submit()

        return Response(KycApplicationSerializer(kyc).data, status=200)
