from rest_framework.routers import DefaultRouter

from apps.sales.sales.views import SaleViewSet

router = DefaultRouter()
router.register(
    'sales',
    SaleViewSet,
    basename='sales'
)

urlpatterns = router.urls

