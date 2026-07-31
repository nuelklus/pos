from django.db import models

from apps.core.tenant.models import TenantBaseModel


class StockMovement(TenantBaseModel):

    class MovementType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        RETURN = "RETURN", "Return"


    class ReferenceType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"
        RETURN = "RETURN", "Return"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        TRANSFER = "TRANSFER", "Transfer"


    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reference_type = models.CharField(
        max_length=20,
        choices=ReferenceType.choices,
        blank=True,
    )

    reference_id = models.UUIDField(
        null=True,
        blank=True
    )


    def __str__(self):
        return f"{self.movement_type} - {self.product} ({self.quantity})"