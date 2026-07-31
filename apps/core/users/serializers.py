
from rest_framework import serializers
from apps.core.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
        )


