
from rest_framework.permissions import BasePermission


class IsTenantUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.tenant is not None
            and getattr(request, "tenant", None) is not None
            and request.user.tenant_id == request.tenant.id
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request, "tenant", None) is not None
            and request.user.tenant_id == request.tenant.id
            and obj.tenant_id == request.tenant.id
        )


class HasModulePermission(BasePermission):
    def has_permission(self, request, view):
        # Implement module/action specific permissions here
        # This will likely involve checking request.user.roles and the requested module/action
        return True

