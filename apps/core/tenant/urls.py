from django.urls import path
from apps.core.tenant.views import TenantView, TenantDetailView

urlpatterns = [
    path("", TenantView.as_view(), name="tenant_list_create"),
    path("<uuid:pk>/", TenantDetailView.as_view(), name="tenant_retrieve_update_destroy"),
]
