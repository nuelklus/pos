
from rest_framework import serializers
from django.db import transaction
from apps.core.tenant.models import Tenant
from apps.core.branch.models import Branch
from apps.core.branch.serializers import BranchSerializer
from apps.core.authentication.models import Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .services import create_default_roles
from django.db import transaction, IntegrityError
User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = (
            "id",
            "name",
        )
        
class UserSerializer(serializers.ModelSerializer):
    tenant = serializers.SerializerMethodField()
    branch = BranchSerializer(read_only=True)
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "tenant",
            "branch",
            "role",
        )

    def get_tenant(self, obj):
        return {
            "id": str(obj.tenant.id),
            "name": obj.tenant.name,
        }

class BusinessRegisterSerializer(serializers.Serializer):

    # Tenant
    business_name = serializers.CharField()
    business_email = serializers.EmailField(
        required=False
    )
    business_phone = serializers.CharField(
        required=False
    )

    branch_name = serializers.CharField()

    branch_location = serializers.CharField(
        required=False,
        allow_blank=True
    )


    # User
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()

    phone_number = serializers.CharField(
        required=False
    )

    password = serializers.CharField(
        write_only=True
    )

    password_confirm = serializers.CharField(
        write_only=True
    )


    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                "Passwords do not match"
            )

        if User.objects.filter(
            email=attrs["email"]
        ).exists():

            raise serializers.ValidationError(
                {
                    "email":
                    "A user with this email already exists."
                }
            )


        if Tenant.objects.filter(
            name=attrs["business_name"]
        ).exists():

            raise serializers.ValidationError(
                {
                    "business_name":
                    "A business with this name already exists."
                }
            )
        return attrs


    @transaction.atomic
    def create(self, validated_data):

        business_name = validated_data.pop(
            "business_name"
        )

        branch_name = validated_data.pop(
            "branch_name"
        )

        branch_location = validated_data.pop(
            "branch_location",
            ""
        )

        password = validated_data.pop(
            "password"
        )

        validated_data.pop(
            "password_confirm"
        )


        try:

            # 1. Create Tenant
            tenant = Tenant.objects.create(
                name=business_name,
            )


            # 2. Create default roles
            roles = create_default_roles(tenant)
            owner_role = roles["Owner"]


            # 3. Create Branch
            branch = Branch.objects.create(
                tenant=tenant,
                name=branch_name,
                location=branch_location
            )


            # 4. Create Owner User
            user = User.objects.create_user(
                tenant=tenant,
                branch=branch,
                role=owner_role,
                password=password,
                **validated_data
            )


            return user


        except IntegrityError as e:

            # rollback happens automatically
            # because of transaction.atomic()

            if "tenant_tenant_name_key" in str(e):

                raise serializers.ValidationError(
                    {
                        "business_name":
                        "A business with this name already exists."
                    }
                )


            raise serializers.ValidationError(
                {
                    "error":
                    "Unable to complete registration. Please try again."
                }
            )    

class StaffRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    role_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                "Passwords do not match"
            )

        if User.objects.filter(
            email=attrs["email"]
        ).exists():
            raise serializers.ValidationError(
                {
                    "email":
                    "A user with this email already exists."
                }
            )

        request = self.context["request"]
        tenant = request.user.tenant
        try:
            role = Role.objects.get(
                id=attrs["role_id"],
                tenant=tenant
            )
            

        except Role.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "role_id":
                    "Invalid role."
                }
            )

        try:
            branch = Branch.objects.get(
                id=attrs["branch_id"],
                tenant=tenant
            )

        except Branch.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "branch_id":
                    "Invalid branch."
                }
            )

        attrs["role"] = role
        attrs["branch"] = branch
        attrs["tenant"] = tenant

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")
        role = validated_data.pop("role")
        branch = validated_data.pop("branch")
        tenant = validated_data.pop("tenant")
        validated_data.pop("role_id")
        validated_data.pop("branch_id")

        user = User.objects.create_user(
            tenant=tenant,
            role=role,
            branch=branch,
            password=password,
            **validated_data
        )

        return user
    
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["tenant_id"] = str(user.tenant.id)
        token["tenant_name"] = user.tenant.name
        return token

    def validate(self, attrs):
        print("LOGIN DATA:", attrs)
        data = super().validate(attrs)
        print("USER:", self.user)

        data["user"] = UserSerializer(self.user).data
        
        return data