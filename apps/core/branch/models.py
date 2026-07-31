from django.db import models
import uuid
# apps/core/tenant/models.py


class Branch(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.CASCADE,
        related_name="branches"
    )

    name = models.CharField(
        max_length=150
    )

    location = models.TextField(
        blank=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return self.name