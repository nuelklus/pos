from django.urls import path

from apps.core.dashboard.views import InventoryDashboardViewSet, OwnerDashboardViewSet

urlpatterns = [
    path(
        "dashboard/",
        OwnerDashboardViewSet.as_view({"get": "list"}),
        name="owner-dashboard",
    ),
    path(
        "inventory/dashboard/",
        InventoryDashboardViewSet.as_view({"get": "list"}),
        name="inventory-dashboard",
    ),
]
