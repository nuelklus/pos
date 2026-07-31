from apps.core.activity.models import ActivityLog


def log_activity(
    *,
    tenant,
    user,
    action,
    module,
    description,
    reference_id=None,
):
    if user and getattr(user, "tenant_id", None) != tenant.id:
        raise ValueError("Activity user does not belong to tenant.")

    return ActivityLog.objects.create(
        tenant=tenant,
        user=user,
        action=action,
        module=module,
        description=description,
        reference_id=reference_id,
        created_by=user,
        updated_by=user,
    )
