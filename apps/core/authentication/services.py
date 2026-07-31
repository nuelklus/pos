from apps.core.authentication.models import Role, RolePermission
from apps.core.permissions.models import Permission


DEFAULT_ROLE_PERMISSIONS = {

    "Owner": "*",


    "Manager": [
        "users.view",

        "products.create",
        "products.view",
        "products.update",

        "sales.create",
        "sales.view",

        "inventory.view",
        "inventory.adjust",
    ],


    "Cashier": [
        "sales.create",
        "sales.view",

        "products.view",
    ],


    "Store Keeper": [
        "products.view",

        "inventory.view",
        "inventory.adjust",
    ],
}



def create_default_roles(tenant):

    created_roles = {}


    permissions = {
        permission.code: permission
        for permission in Permission.objects.all()
    }


    for role_name, role_permissions in DEFAULT_ROLE_PERMISSIONS.items():

        role = Role.objects.create(
            tenant=tenant,
            name=role_name,
            description=f"{role_name} role"
        )


        created_roles[role_name] = role


        # Owner gets every permission
        if role_permissions == "*":

            role_permissions = permissions.keys()


        role_permission_objects = []


        for permission_code in role_permissions:

            permission = permissions.get(
                permission_code
            )


            if permission:

                role_permission_objects.append(
                    RolePermission(
                        role=role,
                        permission=permission
                    )
                )


        RolePermission.objects.bulk_create(
            role_permission_objects
        )


    return created_roles