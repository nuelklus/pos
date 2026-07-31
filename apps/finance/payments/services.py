from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from rest_framework.exceptions import ValidationError

from .models import Payment
from apps.sales.sales.models import Sale


@transaction.atomic
def recalculate_sale_paid_amount(sale):
    """
    Recalculate the total amount paid for a sale and update
    its payment status.
    """

    total_paid = sale.payments.filter(
        is_active=True
    ).aggregate(
        total=Coalesce(
            Sum("amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2,
            ),
        )
    )["total"] or Decimal("0.00")

    sale.paid_amount = total_paid

    if total_paid <= Decimal("0.00"):

        sale.payment_status = Sale.PaymentStatus.UNPAID

    elif total_paid < sale.total_amount:

        sale.payment_status = Sale.PaymentStatus.PARTIAL

    else:

        sale.payment_status = Sale.PaymentStatus.PAID

    sale.save(
        update_fields=[
            "paid_amount",
            "payment_status",
            "updated_at",
        ]
    )

    return sale


@transaction.atomic
def create_payment(
    *,
    tenant,
    user,
    sale,
    amount,
    payment_method,
    reference="",
    notes="",
):
    """
    Record a payment against a completed sale.
    """

    if sale.status != Sale.COMPLETED:
        raise ValidationError(
            "Payments can only be recorded for completed sales."
        )

    amount = Decimal(amount)

    if amount <= Decimal("0.00"):
        raise ValidationError(
            "Payment amount must be greater than zero."
        )

    balance = sale.total_amount - sale.paid_amount

    if amount > balance:
        raise ValidationError(
            f"Payment exceeds outstanding balance of {balance}."
        )

    payment = Payment.objects.create(
        tenant=tenant,
        sale=sale,
        amount=amount,
        payment_method=payment_method,
        reference=reference,
        notes=notes,
        created_by=user,
        updated_by=user,
    )

    recalculate_sale_paid_amount(sale)

    return payment