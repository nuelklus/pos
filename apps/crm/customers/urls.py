from rest_framework.routers import DefaultRouter

from apps.crm.customers.views import CustomerViewSet

router = DefaultRouter()
router.register(
    'customers',
    CustomerViewSet,
    basename='customers'
)

urlpatterns = router.urls

