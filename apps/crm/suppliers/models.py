import uuid

from django.db import models

from apps.core.tenant.models import TenantBaseModel


class Supplier(TenantBaseModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'name'],
                name='unique_supplier_name_per_tenant'
            )
        ]
        indexes = [
            models.Index(
                fields=['tenant', 'name'],
                name='supplier_tenant_name_idx'
            )
        ]

    def __str__(self):
        return self.name

