import uuid
from django.db import models
from apps.core.tenant.models import TenantBaseModel


class Category(TenantBaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant","name"],
                name="unique_category_per_tenant"
            )
        ]

    def __str__(self):
        return self.name
    
class Brand(TenantBaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[ "tenant","name"],
                name="unique_brand_per_tenant"
            )
        ]

    def __str__(self):
        return self.name

class Unit(TenantBaseModel):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant","name"],
                name="unique_unit_per_tenant"
            )
        ]

    def __str__(self):
        return self.name
    
class Product(TenantBaseModel):
    category = models.ForeignKey(Category,on_delete=models.PROTECT,related_name="products")
    brand = models.ForeignKey(Brand,on_delete=models.PROTECT,related_name="products",null=True,blank=True)
    unit = models.ForeignKey(Unit,on_delete=models.PROTECT,related_name="products")
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100,blank=True)
    barcode = models.CharField(max_length=100,blank=True)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    selling_price = models.DecimalField(max_digits=12,decimal_places=2)
    minimum_stock = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    current_stock = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"],name="unique_product_name_per_tnt",),
            models.UniqueConstraint(fields=["tenant", "sku"],name="unique_product_sku_per_tnt",condition=~models.Q(sku="")),
            models.UniqueConstraint(fields=["tenant", "barcode"],name="unique_product_barcode_per_tnt",condition=~models.Q(barcode="")),
        ]