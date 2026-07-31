from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.inventory.stock_movements.services import create_stock_movement
from apps.sales.sales.models import Sale
from apps.finance.payments.models import Payment
from apps.finance.payments.services import (
    create_payment,
    recalculate_sale_paid_amount,
)

def generate_invoice_number(tenant):

    last_sale = Sale.objects.filter(
        tenant=tenant,
        is_active=True,
    ).order_by(
        "-created_at"
    ).first()


    if not last_sale or not last_sale.invoice_number:

        number = 1


    else:

        try:

            parts = last_sale.invoice_number.split("-")


            if len(parts) == 2:

                number = int(parts[1]) + 1

            else:

                number = 1


        except (ValueError, IndexError):

            number = 1



    return f"INV-{number:06d}"

@transaction.atomic
def complete_sale(
    sale,
    request,
    payment_data=None,
):

    if sale.status != Sale.DRAFT:

        raise ValueError(
            "Only draft sales can be completed."
        )


    # ==========================
    # STOCK DEDUCTION
    # ==========================

    for item in sale.items.all():

        product = item.product


        if product.current_stock < item.quantity:

            raise ValueError(
                f"Insufficient stock for {product.name}. "
                f"Available: {product.current_stock}, "
                f"Requested: {item.quantity}"
            )


        create_stock_movement(
            tenant=request.tenant,
            branch=sale.branch,
            user=request.user,
            product=product,
            movement_type="SALE",
            quantity=-item.quantity,
            reference_type="Sale",
            reference_id=sale.id,
        )


    # ==========================
    # COMPLETE SALE
    # ==========================

    sale.status = Sale.COMPLETED

    sale.updated_by = request.user


    sale.save(
        update_fields=[
            "status",
            "updated_by",
            "updated_at",
        ]
    )


    # ==========================
    # CREATE INITIAL PAYMENT
    # ==========================

    if payment_data:

        create_payment(
            tenant=request.tenant,
            user=request.user,
            sale=sale,
            amount=payment_data["amount"],
            payment_method=payment_data["payment_method"],
            reference=payment_data.get(
                "reference",
                ""
            ),
            notes=payment_data.get(
                "notes",
                ""
            ),
        )


    else:

        # No payment received
        # Set UNPAID status

        recalculate_sale_paid_amount(
            sale
        )


    return sale