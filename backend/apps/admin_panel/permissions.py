from rest_framework.permissions import BasePermission

from .models import AdminUser


class IsAdminAuthenticated(BasePermission):
    message = "احراز هویت مدیر الزامی است."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.user, AdminUser)
            and request.auth
            and request.auth.get("account_type") == "admin"
        )


class IsSuperAdmin(BasePermission):
    message = "دسترسی مدیر ارشد مورد نیاز است."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.user, AdminUser)
            and request.user.role == "super_admin"
        )