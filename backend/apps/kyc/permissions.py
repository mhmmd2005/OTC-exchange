from rest_framework.permissions import BasePermission


class IsKycOwner(BasePermission):
    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        return (
            request.user.is_authenticated
            and obj.user_id == request.user.id
        )


class IsAdminUser(BasePermission):
    message = "دسترسی مدیریت مورد نیاز است."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsKycVerified(BasePermission):
    message = (
        "برای انجام این عملیات ابتدا باید "
        "احراز هویت خود را تکمیل کنید."
    )

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.kyc_status == "approved"
        )