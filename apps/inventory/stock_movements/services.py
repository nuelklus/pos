from decimal import Decimal

from django.db import transaction

from apps.core.activity.services import log_activity
from apps.inventory.products.models import Product
from apps.inventory.stock_movements.models import StockMovement



@transaction.atomic
def create_stock_movement(
    *,
    tenant,
    user,
    branch,
    product,
    movement_type,
    quantity,
    reference_type=None,
    reference_id=None,
):

    if quantity is None:
        raise ValueError(
            "Quantity is required."
        )


    quantity = Decimal(quantity)


    if quantity == 0:
        raise ValueError(
            "Quantity cannot be zero."
        )


    if product.tenant_id != tenant.id:
        raise ValueError(
            "Invalid product tenant."
        )


    if branch.tenant_id != tenant.id:
        raise ValueError(
            "Invalid branch tenant."
        )


    # lock product row before changing stock
    product = Product.objects.select_for_update().get(
        id=product.id,
        tenant=tenant,
        is_active=True,
    )


    # prevent negative stock
    if quantity < 0 and product.current_stock < abs(quantity):
        raise ValueError(
            f"Insufficient stock for {product.name}"
        )


    product.current_stock += quantity
    product.updated_by = user


    product.save(
        update_fields=[
            "current_stock",
            "updated_by",
        ]
    )


    stock_movement = StockMovement.objects.create(
        tenant=tenant,
        branch=branch,
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type or "",
        reference_id=reference_id,
        created_by=user,
        updated_by=user,
    )

    if str(movement_type).upper() == StockMovement.MovementType.ADJUSTMENT:
        log_activity(
            tenant=tenant,
            user=user,
            action="ADJUSTED",
            module="STOCK",
            description=f"Adjusted stock for {product.name} by {quantity}.",
            reference_id=stock_movement.id,
        )

    return stock_movement