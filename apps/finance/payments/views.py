from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.core.activity.services import log_activity
from apps.finance.payments.models import Payment
from apps.finance.payments.serializers import PaymentSerializer
from apps.finance.payments.services import create_payment


class PaymentViewSet(viewsets.ModelViewSet):

    serializer_class = PaymentSerializer
    lookup_field = "id"


    def get_queryset(self):

        if not self.request.tenant:

            return Payment.objects.none()


        return Payment.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).order_by(
            "-created_at"
        )



    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request
            }
        )


        serializer.is_valid(
            raise_exception=True
        )


        payment = create_payment(

            tenant=request.tenant,

            user=request.user,

            sale=serializer.validated_data["sale"],

            amount=serializer.validated_data["amount"],

            payment_method=serializer.validated_data["payment_method"],

            reference=serializer.validated_data.get(
                "reference",
                ""
            ),

            notes=serializer.validated_data.get(
                "notes",
                ""
            ),
        )


        output_serializer = self.get_serializer(
            payment
        )
        log_activity(
            tenant=request.tenant,
            user=request.user,
            action="RECEIVED",
            module="PAYMENT",
            description=f"Received payment {payment.amount} for sale {payment.sale.invoice_number}.",
            reference_id=payment.id,
        )


        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )



    def perform_update(self, serializer):

        payment = serializer.save(
            updated_by=self.request.user
        )


        # Recalculate after editing payment

        from apps.finance.payments.services import (
            recalculate_sale_paid_amount
        )


        recalculate_sale_paid_amount(
            payment.sale
        )



    def perform_destroy(self, instance):

        sale = instance.sale


        instance.is_active = False

        instance.updated_by = self.request.user

        instance.save(
            update_fields=[
                "is_active",
                "updated_by",
                "updated_at",
            ]
        )


        # Recalculate after deleting payment

        from apps.finance.payments.services import (
            recalculate_sale_paid_amount
        )


        recalculate_sale_paid_amount(
            sale
        )