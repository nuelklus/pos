from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import StockMovement
from .serializers import StockMovementSerializer


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if not getattr(self.request, 'tenant', None):
            return StockMovement.objects.none()

        return StockMovement.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).select_related('branch', 'product').order_by('-created_at')

