
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from .managers import UserManager
    
class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenant.Tenant", on_delete=models.CASCADE, related_name="users")
    role = models.ForeignKey("authentication.Role", on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    branch = models.ForeignKey("branch.Branch", on_delete=models.SET_NULL,null=True,blank=True,related_name="users")
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # def has_permission(self, permission_code):

    #     if not self.role:
    #         return False
    #     return self.role.permissions.filter(
    #         permission__code=permission_code
    #     ).exists()


    def __str__(self):
        return self.email