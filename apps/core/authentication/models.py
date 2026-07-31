import uuid
from django.db import models

class Role(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    tenant = models.ForeignKey("tenant.Tenant",on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["tenant","name"],
                name="unique_role_per_tenant"
            )
        ]

    def __str__(self):
        return self.name

class RolePermission(models.Model):
    role = models.ForeignKey( Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.ForeignKey("permissions.Permission",on_delete=models.CASCADE,related_name="roles")
    created_at = models.DateTimeField( auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role","permission"],
                name="unique_role_permission"
            )
        ]