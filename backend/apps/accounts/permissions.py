from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return True
        if hasattr(obj, "user"):
            return obj.user_id == request.user.id
        return obj == request.user
