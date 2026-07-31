import uuid
from django.db import models

class Permission(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    module = models.CharField( max_length=50)
    action = models.CharField( max_length=50)
    name = models.CharField(max_length=100)
    code = models.CharField( max_length=100,unique=True)
    description = models.TextField( blank=True)

    def __str__(self):
        return self.code