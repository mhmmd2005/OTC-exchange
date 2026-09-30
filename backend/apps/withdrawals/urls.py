from django.urls import path

from .views import (
    WithdrawalAddressConfirmationAPIView,
    WithdrawalAddressDetailAPIView,
    WithdrawalAddressListCreateAPIView,
    WithdrawalAddressResendConfirmationAPIView,
    WithdrawalAddressSetDefaultAPIView,
)


urlpatterns = [
    path(
        "addresses",
        WithdrawalAddressListCreateAPIView.as_view(),
        name="withdrawal-address-list-create",
    ),
    path(
        "addresses/<int:pk>",
        WithdrawalAddressDetailAPIView.as_view(),
        name="withdrawal-address-detail",
    ),
    path(
        "addresses/<int:pk>/confirm",
        WithdrawalAddressConfirmationAPIView.as_view(),
        name="withdrawal-address-confirm",
    ),
    path(
        "addresses/<int:pk>/resend-confirmation",
        WithdrawalAddressResendConfirmationAPIView.as_view(),
        name="withdrawal-address-resend-confirmation",
    ),
    path(
        "addresses/<int:pk>/set-default",
        WithdrawalAddressSetDefaultAPIView.as_view(),
        name="withdrawal-address-set-default",
    ),
]