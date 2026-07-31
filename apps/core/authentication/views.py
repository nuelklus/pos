
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.core.authentication.permissions import HasStaffCreatePermission
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from apps.core.authentication.serializers import (
    BusinessRegisterSerializer,
    LoginSerializer,
    UserSerializer,
    StaffRegistrationSerializer,
    RoleSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets
from apps.core.authentication.models import Role

User = get_user_model()


class BusinessRegisterView(generics.CreateAPIView):

    serializer_class = BusinessRegisterSerializer
    permission_classes = [AllowAny]


    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Registration completed successfully.",

                "access": str(refresh.access_token),
                "refresh": str(refresh),

                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

class StaffRegistrationView(generics.CreateAPIView):
    serializer_class = StaffRegistrationSerializer
    permission_classes = [IsAuthenticated, HasStaffCreatePermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "Staff registration completed successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class RoleViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    lookup_field = "id"

    def get_queryset(self):

        return Role.objects.filter(
            tenant=self.request.tenant
        ).order_by("name")