from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.activity.services import log_activity
from apps.core.permissions.permissions import IsTenantUser
from apps.finance.payments.models import Payment
from apps.sales.receipts.serializers import ReceiptSerializer
from apps.sales.sales.models import Sale
from apps.sales.sales.serializers import SaleSerializer
from apps.sales.sales.services import (
    generate_invoice_number,
    complete_sale,
)


class SaleViewSet(viewsets.ModelViewSet):

    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    lookup_field = "id"


    def get_queryset(self):

        if not getattr(self.request, "tenant", None):
            return Sale.objects.none()


        return Sale.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).select_related(
            "customer",
            "branch",
            "tenant",
        ).prefetch_related(
            "items__product"
        ).order_by(
            "-sale_date"
        )



    def perform_create(self, serializer):

        invoice_number = generate_invoice_number(
            self.request.tenant
        )


        sale = serializer.save(

            tenant=self.request.tenant,

            invoice_number=invoice_number,

            created_by=self.request.user,

            updated_by=self.request.user,

        )
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="CREATED",
            module="SALE",
            description=f"Created sale {sale.invoice_number}.",
            reference_id=sale.id,
        )



    def perform_update(self, serializer):

        serializer.save(

            updated_by=self.request.user,

        )



    def perform_destroy(self, instance):

        if instance.status != Sale.DRAFT:

            raise ValueError(
                "Only draft sales can be deleted."
            )


        instance.is_active = False

        instance.updated_by = self.request.user


        instance.save(
            update_fields=[
                "is_active",
                "updated_by",
                "updated_at",
            ]
        )



    @action(detail=True, methods=["post"])
    def complete(self, request, id=None):

        sale = self.get_object()


        payment_data = request.data.get(
            "payment"
        )


        try:

            completed_sale = complete_sale(

                sale=sale,

                request=request,

                payment_data=payment_data,

            )


            serializer = self.get_serializer(
                completed_sale
            )
            log_activity(
                tenant=request.tenant,
                user=request.user,
                action="COMPLETED",
                module="SALE",
                description=f"Completed sale {completed_sale.invoice_number}.",
                reference_id=completed_sale.id,
            )


            return Response(

                {
                    "message": "Sale completed successfully.",
                    "sale": serializer.data,
                },

                status=status.HTTP_200_OK

            )


        except ValueError as e:

            return Response(

                {
                    "error": str(e)
                },

                status=status.HTTP_400_BAD_REQUEST

            )

    @action(
        detail=True,
        methods=["get"],
        url_path="receipt",
    )
    def receipt(self, request, id=None):
        sale = self.get_object()
        sale = self.get_queryset().prefetch_related(
            Prefetch(
                "payments",
                queryset=Payment.objects.filter(
                    is_active=True,
                ).only(
                    "id",
                    "sale_id",
                    "amount",
                    "payment_method",
                    "created_at",
                    "payment_date",
                ),
            ),
        ).get(id=sale.id)

        if sale.status != Sale.COMPLETED:
            raise ValidationError(
                "Receipt is only available for completed sales."
            )

        serializer = ReceiptSerializer(
            sale,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)