from django.db import models
from django.utils import timezone

from apps.core.tenant.models import TenantBaseModel


class Purchase(TenantBaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        RECEIVED = 'RECEIVED', 'Received'
        CANCELLED = 'CANCELLED', 'Cancelled'

    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    invoice_number = models.CharField(max_length=100)
    purchase_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'invoice_number'],
                name='unique_purchase_invoice_per_tenant'
            )
        ]

    def __str__(self):
        return f'{self.invoice_number} - {self.supplier}'


class PurchaseItem(TenantBaseModel):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='purchase_items'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.product} x {self.quantity}'

