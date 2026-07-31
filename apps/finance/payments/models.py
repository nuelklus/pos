from decimal import Decimal

from django.db import models

from apps.core.tenant.models import TenantBaseModel


class Payment(TenantBaseModel):
    CASH = 'CASH'
    MOBILE_MONEY = 'MOBILE_MONEY'
    BANK = 'BANK'

    PAYMENT_METHOD_CHOICES = [
        (CASH, 'Cash'),
        (MOBILE_MONEY, 'Mobile Money'),
        (BANK, 'Bank'),
    ]

    sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
    )
    reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    payment_date = models.DateTimeField(
            auto_now_add=True
        )
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'sale']),
            models.Index(fields=['tenant', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sale.invoice_number} - {self.amount} ({self.payment_method})'

