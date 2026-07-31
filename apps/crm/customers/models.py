from django.db import models
from django.utils.text import slugify

from apps.core.tenant.models import TenantBaseModel


class Customer(TenantBaseModel):
    customer_code = models.CharField(
        max_length=20,
        unique=False,
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'name'],
                name='unique_customer_name_per_tenant'
            ),
            models.UniqueConstraint(
                fields=['tenant', 'customer_code'],
                name='unique_customer_code_per_tenant'
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'phone']),
            models.Index(fields=['tenant', 'customer_code']),
        ]

    def __str__(self):
        return f'{self.customer_code} - {self.name}'

