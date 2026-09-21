from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..authentication import AdminJWTAuthentication
from ..permissions import IsAdminAuthenticated
from ..serializers import (
    AdminIdentitySerializer,
    AdminLoginSerializer,
    AdminLogoutSerializer,
    AdminRefreshSerializer,
)
from ..services.auth import AdminAuthService


class AdminLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AdminAuthService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            request=request,
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class AdminRefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminRefreshSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AdminAuthService.refresh(
            serializer.validated_data["refresh"]
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class AdminLogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLogoutSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AdminAuthService.logout(
            serializer.validated_data["refresh"]
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class AdminMeAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication
    ]

    permission_classes = [
        IsAdminAuthenticated
    ]

    def get(self, request):
        return Response(
            AdminIdentitySerializer(
                request.user
            ).data,
            status=status.HTTP_200_OK,
        )