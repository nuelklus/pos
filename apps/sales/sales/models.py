from decimal import Decimal

from django.db import models

from apps.core.tenant.models import TenantBaseModel


class Sale(TenantBaseModel):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]
    class PaymentStatus(models.TextChoices):
            UNPAID = "UNPAID", "Unpaid"
            PARTIAL = "PARTIAL", "Partial"
            PAID = "PAID", "Paid"

    invoice_number = models.CharField(max_length=20)

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="sales",
    )

    branch = models.ForeignKey(
        "branch.Branch",
        on_delete=models.PROTECT,
        related_name="sales",
    )

    sale_date = models.DateTimeField(auto_now_add=True)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        ) 
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tenant",
                    "invoice_number",
                ],
                name="unique_invoice_number_per_tenant",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "tenant",
                    "invoice_number",
                ]
            ),
            models.Index(
                fields=[
                    "tenant",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "tenant",
                    "sale_date",
                ]
            ),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"


class SaleItem(TenantBaseModel):

    class DiscountType(models.TextChoices):
        NONE = "NONE", "No Discount"
        AMOUNT = "AMOUNT", "Fixed Amount"
        PERCENTAGE = "PERCENTAGE", "Percentage"
        
    
    
    sale = models.ForeignKey(
        "Sale",
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    # Snapshot of Product.selling_price
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.NONE,
    )

    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Actual selling price after discount
    final_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=["sale", "product"],
            name="unique_product_per_sale",
        ),
        ]
        indexes = [
            models.Index(fields=["tenant","sale",]),
            models.Index(fields=["tenant","product",]),
        ]

    def __str__(self):
        return f"{self.sale.invoice_number} - {self.product.name}"