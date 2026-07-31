from django.db import migrations


def create_permissions(apps, schema_editor):

    Permission = apps.get_model(
        "permissions",
        "Permission"
    )


    permissions = [
        ("users.create", "users", "create"),
        ("users.view", "users", "view"),
        ("users.update", "users", "update"),
        ("users.delete", "users", "delete"),

        ("products.create", "products", "create"),
        ("products.view", "products", "view"),
        ("products.update", "products", "update"),
        ("products.delete", "products", "delete"),

        ("sales.create", "sales", "create"),
        ("sales.view", "sales", "view"),

        ("inventory.view", "inventory", "view"),
        ("inventory.adjust", "inventory", "adjust"),
    ]


    for code, module, action in permissions:

        Permission.objects.get_or_create(
            code=code,
            defaults={
                "module": module,
                "action": action,
            }
        )


def remove_permissions(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("permissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_permissions,
            remove_permissions
        )
    ]