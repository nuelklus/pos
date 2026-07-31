from rest_framework import serializers
from .models import Category, Brand, Unit, Product
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        
    def validate_name(self, value):

        request = self.context.get("request")

        if request and hasattr(request, "tenant"):

            exists = Category.objects.filter(
                tenant=request.tenant,
                name__iexact=value
            ).exists()

            if exists:
                raise serializers.ValidationError(
                    "A category with this name already exists."
                )

        return value

class BrandSerializerInResponse(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
        ]
            
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
        ]
    
    def validate_name(self, value):

        request = self.context.get("request")

        if not request:
            return value


        tenant = request.tenant


        queryset = Brand.objects.filter(
            tenant=tenant,
            name__iexact=value.strip()
        )


        # Ignore current object during update
        if self.instance:

            queryset = queryset.exclude(
                id=self.instance.id
            )


        if queryset.exists():

            raise serializers.ValidationError(
                "A brand with this name already exists."
            )

        return value.strip()

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "name",
            "short_name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        request = self.context.get("request")
        queryset = Unit.objects.filter(
            tenant=request.tenant,
            name__iexact=value.strip()
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError(
                "A unit with this name already exists."
            )

        return value.strip()    

class CategorySerializerInResponse(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
        ]
 
class UnitSerializerInResponse(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = [
            "id",
            "name",
            "short_name",
        ]
                    
class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(write_only=True)
    brand_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True
    )
    unit_id = serializers.UUIDField(write_only=True)
    category = CategorySerializerInResponse(read_only=True)
    brand = BrandSerializerInResponse(read_only=True)
    unit = UnitSerializerInResponse(read_only=True)


    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_id",
            "brand",
            "brand_id",
            "unit",
            "unit_id",
            "name",
            "sku",
            "barcode",
            "description",
            "cost_price",
            "selling_price",
            "minimum_stock",
            "current_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "current_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        request = self.context["request"]
        tenant = request.tenant


        # =========================
        # Category
        # =========================

        category_id = attrs.pop(
            "category_id",
            None
        )

        if category_id:

            try:
                attrs["category"] = Category.objects.get(
                    id=category_id,
                    tenant=tenant,
                    is_active=True
                )

            except Category.DoesNotExist:

                raise serializers.ValidationError(
                    {
                        "category_id": "Invalid category."
                    }
                )

        elif not self.instance:

            # Required only during creation
            raise serializers.ValidationError(
                {
                    "category_id": "This field is required."
                }
            )


        # =========================
        # Brand
        # =========================

        brand_id = attrs.pop(
            "brand_id",
            None
        )


        if brand_id:

            try:
                attrs["brand"] = Brand.objects.get(
                    id=brand_id,
                    tenant=tenant,
                    is_active=True
                )

            except Brand.DoesNotExist:

                raise serializers.ValidationError(
                    {
                        "brand_id": "Invalid brand."
                    }
                )


        elif "brand_id" in self.initial_data:

            # User intentionally removed brand
            attrs["brand"] = None



        # =========================
        # Unit
        # =========================

        unit_id = attrs.pop(
            "unit_id",
            None
        )


        if unit_id:

            try:
                attrs["unit"] = Unit.objects.get(
                    id=unit_id,
                    tenant=tenant,
                    is_active=True
                )

            except Unit.DoesNotExist:

                raise serializers.ValidationError(
                    {
                        "unit_id": "Invalid unit."
                    }
                )


        elif not self.instance:

            # Required only during creation
            raise serializers.ValidationError(
                {
                    "unit_id": "This field is required."
                }
            )


        # =========================
        # Duplicate checks
        # =========================

        queryset = Product.objects.filter(
            tenant=tenant
        )


        if self.instance:

            queryset = queryset.exclude(
                id=self.instance.id
            )


        # Product name

        name = attrs.get("name")

        if name:

            if queryset.filter(
                name__iexact=name.strip()
            ).exists():

                raise serializers.ValidationError(
                    {
                        "name": "Product name already exists."
                    }
                )


        # SKU

        sku = attrs.get("sku")

        if sku:

            if queryset.filter(
                sku__iexact=sku.strip()
            ).exists():

                raise serializers.ValidationError(
                    {
                        "sku": "SKU already exists."
                    }
                )


        # Barcode

        barcode = attrs.get("barcode")

        if barcode:

            if queryset.filter(
                barcode=barcode
            ).exists():

                raise serializers.ValidationError(
                    {
                        "barcode": "Barcode already exists."
                    }
                )


        return attrs