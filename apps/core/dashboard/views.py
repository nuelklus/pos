from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions.permissions import IsTenantUser
from apps.core.dashboard.serializers import InventoryDashboardSerializer, OwnerDashboardSerializer
from apps.core.dashboard.services import get_inventory_dashboard_data, get_owner_dashboard_data


class OwnerDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def list(self, request):
        if not getattr(request, "tenant", None):
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)

        payload = get_owner_dashboard_data(tenant=request.tenant)
        serializer = OwnerDashboardSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def list(self, request):
        if not getattr(request, "tenant", None):
            return Response({"detail": "Tenant not found."}, status=status.HTTP_400_BAD_REQUEST)

        payload = get_inventory_dashboard_data(tenant=request.tenant)
        serializer = InventoryDashboardSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
