from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BrandViewSet, UnitViewSet, ProductViewSet

router = DefaultRouter()

router.register("categories", CategoryViewSet, basename="categories")
router.register("brands", BrandViewSet, basename="brands")
router.register("units", UnitViewSet, basename="units")
router.register("products", ProductViewSet, basename="products")
urlpatterns = router.urls