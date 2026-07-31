
from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework.routers import DefaultRouter
from apps.core.authentication.views import (LoginView, BusinessRegisterView, MeView, StaffRegistrationView, RoleViewSet)

router = DefaultRouter()

router.register(
    "roles",
    RoleViewSet,
    basename="roles"
)
urlpatterns = [
    path("register/", BusinessRegisterView.as_view(), name="auth_register"),
    path("staff/register/", StaffRegistrationView.as_view(), name="staff_register"),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("logout/", TokenBlacklistView.as_view(), name="auth_logout"),
    path("me/", MeView.as_view(), name="auth_me"),  
]

urlpatterns += router.urls