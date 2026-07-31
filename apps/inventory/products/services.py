from django.db import transaction


@transaction.atomic
def update_product_cost_price(
    product,
    new_cost_price,
    user=None,
):

    if new_cost_price is None:
        return product

    if product.cost_price == new_cost_price:
        return product

    product.cost_price = new_cost_price

    if user:
        product.updated_by = user

    update_fields = [
        "cost_price",
    ]

    if user:
        update_fields.append(
            "updated_by"
        )

    product.save(
        update_fields=update_fields
    )

    return product