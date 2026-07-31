from rest_framework.routers import DefaultRouter

from apps.finance.payments.views import PaymentViewSet

router = DefaultRouter()
router.register(
    'payments',
    PaymentViewSet,
    basename='payments'
)

urlpatterns = router.urls

