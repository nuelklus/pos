from decimal import Decimal

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.activity.services import log_activity
from apps.inventory.stock_movements.services import create_stock_movement
from .models import Purchase
from .serializers import PurchaseSerializer
from apps.inventory.products.services import (
    update_product_cost_price
)
class PurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if not getattr(self.request, 'tenant', None):
            return Purchase.objects.none()

        return Purchase.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).select_related('supplier', 'branch').prefetch_related('items__product').order_by('-created_at')

    def perform_create(self, serializer):
        purchase = serializer.save(tenant=self.request.tenant, created_by=self.request.user,
            updated_by=self.request.user,)
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="CREATED",
            module="PURCHASE",
            description=f"Created purchase {purchase.invoice_number}.",
            reference_id=purchase.id,
        )
        
    def perform_update(self, serializer):

        serializer.save(
            updated_by=self.request.user
        )
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=True, methods=["post"])
    def receive(self, request, id=None):

        purchase = self.get_object()


        if purchase.status != Purchase.Status.DRAFT:
            return Response(
                {
                    "detail": "Only draft purchases can be received."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        with transaction.atomic():

            total_amount = Decimal("0")


            for item in purchase.items.all():

                product = item.product


                if not product.is_active:
                    return Response(
                        {
                            "detail": f"Product '{product.name}' is inactive."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )


                # 1. Create stock movement
                create_stock_movement(
                    tenant=request.tenant,
                    user=request.user,
                    branch=purchase.branch,
                    product=product,
                    movement_type="PURCHASE",
                    quantity=item.quantity,
                    reference_type="Purchase",
                    reference_id=purchase.id,
                )


                # 2. Update product cost price only
                update_product_cost_price(
                    product=product,
                    new_cost_price=item.cost_price,
                    user=request.user,
                )


                total_amount += item.subtotal



            # 3. Mark purchase as received
            purchase.status = Purchase.Status.RECEIVED

            purchase.total_amount = total_amount

            purchase.updated_by = request.user


            purchase.save(
                update_fields=[
                    "status",
                    "total_amount",
                    "updated_by",
                ]
            )


        serializer = self.get_serializer(purchase)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )