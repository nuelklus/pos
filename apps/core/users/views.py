
from rest_framework import viewsets
from apps.core.users.models import User
from apps.core.users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
