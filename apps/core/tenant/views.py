from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.core.tenant.models import Tenant
from apps.core.tenant.serializers import TenantSerializer

class TenantView(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)

class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated,)
