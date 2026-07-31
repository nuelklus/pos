
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/tenant/", include("apps.core.tenant.urls")),
    path("api/users/", include("apps.core.users.urls")),
    path("api/auth/", include("apps.core.authentication.urls")),
    path("api/", include("apps.core.dashboard.urls")),
    path("api/", include("apps.core.activity.urls")),
    path("api/", include("apps.crm.suppliers.urls")),
    path("api/", include("apps.crm.customers.urls")),
    path("api/", include("apps.sales.sales.urls")),
    path("api/", include("apps.finance.payments.urls")),
    # path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/",include("apps.core.branch.urls")),
    path("api/",include("apps.purchasing.purchases.urls")),
    path("api/",include("apps.inventory.stock_movements.urls")),
    path("api/",include("apps.inventory.products.urls")),
    # path("api/organization/branches/", include("apps.organization.branches.urls")),
    # path("api/catalog/categories/", include("apps.catalog.categories.urls")),
    # path("api/catalog/brands/", include("apps.catalog.brands.urls")),
    # path("api/catalog/units/", include("apps.catalog.units.urls")),
    # path("api/catalog/products/", include("apps.catalog.products.urls")),
    # path("api/inventory/stock/", include("apps.inventory.stock.urls")),
    # path("api/inventory/stock_movements/", include("apps.inventory.stock_movements.urls")),
    # path("api/crm/customers/", include("apps.crm.customers.urls")),
    # path("api/crm/suppliers/", include("apps.crm.suppliers.urls")),
    # path("api/purchasing/purchases/", include("apps.purchasing.purchases.urls")),
    # path("api/sales/sales/", include("apps.sales.sales.urls")),
    # path("api/sales/payments/", include("apps.sales.payments.urls")),
    # path("api/sales/receipts/", include("apps.sales.receipts.urls")),
    # path("api/reports/", include("apps.reports.urls")),
]
