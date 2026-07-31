from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.activity.services import log_activity
from .models import Category, Brand, Unit, Product
from .serializers import CategorySerializer, BrandSerializer, UnitSerializer, ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Category.objects.filter(
            tenant=self.request.tenant,
            is_active=True
        ).order_by(
            "name"
        )

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(
            update_fields=[
                "is_active"
            ]
        )
        
class BrandViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Brand.objects.filter(
            tenant=self.request.tenant,
            is_active=True
        ).order_by(
            "name"
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(
            update_fields=["is_active"]
        )

class UnitViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Unit.objects.filter(
            tenant=self.request.tenant,
            is_active=True
        ).order_by(
            "name"
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        
class ProductViewSet(viewsets.ModelViewSet):
    # pagination_class = None
    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated
    ]

    lookup_field = "id"


    def get_queryset(self):

        return Product.objects.filter(
            tenant=self.request.tenant,
            is_active=True
        ).select_related(
            "category",
            "brand",
            "unit"
        ).order_by(
            "name"
        )


    def perform_create(self, serializer):

        product = serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="CREATED",
            module="PRODUCT",
            description=f"Added product {product.name}.",
            reference_id=product.id,
        )

    def perform_update(self, serializer):

        product = serializer.save(
            updated_by=self.request.user
        )
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="UPDATED",
            module="PRODUCT",
            description=f"Updated product {product.name}.",
            reference_id=product.id,
        )

    def perform_destroy(self, instance):

        instance.is_active = False

        instance.save(
            update_fields=[
                "is_active"
            ]
        )
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="DELETED",
            module="PRODUCT",
            description=f"Deleted product {instance.name}.",
            reference_id=instance.id,
        )