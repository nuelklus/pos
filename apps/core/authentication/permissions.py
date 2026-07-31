from rest_framework import permissions
from .models import RolePermission

class HasStaffCreatePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        return RolePermission.objects.filter(
            role=user.role,
            permission__code="users.create"
        ).exists()