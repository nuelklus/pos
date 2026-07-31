from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Branch
from .serializers import BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):

    serializer_class = BranchSerializer

    permission_classes = [
        IsAuthenticated
    ]

    lookup_field = "id"


    def get_queryset(self):

        return Branch.objects.filter(
            tenant=self.request.tenant, is_active=True
        ).order_by(
            "name"
        )


    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant
        )


    def perform_destroy(self, instance):

        # Soft delete
        instance.is_active = False
        instance.save(
            update_fields=[
                "is_active"
            ]
        )