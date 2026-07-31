from rest_framework.permissions import BasePermission


class HasTenantContext(BasePermission):
    """Ensure authenticated requests include an active tenant context."""

    def has_permission(self, request, view):
        return (
            bool(request.user and request.user.is_authenticated)
            and hasattr(request, "tenant")
            and request.tenant is not None
        )

    def has_object_permission(self, request, view, obj):
        return (
            bool(request.user and request.user.is_authenticated)
            and hasattr(obj, "tenant")
            and request.tenant is not None
            and obj.tenant_id == request.tenant.id
        )
