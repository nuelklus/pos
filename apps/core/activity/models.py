from django.conf import settings
from django.db import models

from apps.core.tenant.models import TenantBaseModel


class ActivityLog(TenantBaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=64)
    module = models.CharField(max_length=64)
    description = models.TextField()
    reference_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "module"]),
            models.Index(fields=["tenant", "action"]),
        ]

    def __str__(self):
        return f"{self.module}:{self.action}"
