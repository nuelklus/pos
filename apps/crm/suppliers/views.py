from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if not getattr(self.request, 'tenant', None):
            return Supplier.objects.none()

        return Supplier.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).order_by('name')

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

