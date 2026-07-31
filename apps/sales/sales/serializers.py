from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from apps.crm.customers.models import Customer
from apps.crm.customers.services import generate_customer_code
from apps.inventory.products.models import Product
from apps.sales.sales.models import Sale, SaleItem
from apps.core.branch.models import Branch


class SaleItemSerializer(serializers.ModelSerializer):

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source="product",
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        model = SaleItem

        fields = [
            "id",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "discount_type",
            "discount_value",
            "final_price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "unit_price",
            "final_price",
            "subtotal",
        ]


    def validate_quantity(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        return value


    def validate_discount_value(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Discount value cannot be negative."
            )

        return value


    def validate(self, attrs):

        discount_type = attrs.get(
            "discount_type",
            SaleItem.DiscountType.NONE
        )

        discount_value = attrs.get(
            "discount_value",
            Decimal("0.00")
        )


        if discount_type == SaleItem.DiscountType.PERCENTAGE:

            if discount_value > 100:
                raise serializers.ValidationError(
                    {
                        "discount_value":
                        "Percentage discount cannot exceed 100%."
                    }
                )


        return attrs



class SaleSerializer(serializers.ModelSerializer):

    items = SaleItemSerializer(
        many=True,
        write_only=True
    )

    items_detail = serializers.SerializerMethodField(
        read_only=True
    )


    customer_data = serializers.SerializerMethodField(
        read_only=True
    )


    customer_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )


    customer = serializers.DictField(
        write_only=True,
        required=False,
        allow_null=True,
    )


    branch_id = serializers.UUIDField(
        write_only=True,
        required=True,
        allow_null=True,
    )


    branch = serializers.SerializerMethodField(
        read_only=True
    )

    payment_status = serializers.CharField(
        read_only=True
    )
    
    balance = serializers.SerializerMethodField()



    class Meta:

        model = Sale

        fields = [

            "id",

            "invoice_number",

            "customer_id",

            "customer",

            "customer_data",

            "branch_id",

            "branch",

            "sale_date",

            "total_amount",
            "balance",
            "payment_status",
            "paid_amount",

            "status",

            "remarks",

            "items",

            "items_detail",

        ]


        read_only_fields = [

            "id",

            "invoice_number",

            "branch",

            "sale_date",

            "total_amount",

            "paid_amount",

            "status",

        ]



    def get_branch(self, obj):

        return {

            "id": str(obj.branch.id),

            "name": obj.branch.name,

        }



    def get_items_detail(self, obj):

        return SaleItemSerializer(
            obj.items.all(),
            many=True
        ).data

    def get_balance(self, obj: Sale):

        balance = (
            obj.total_amount or Decimal("0.00")
        ) - (
            obj.paid_amount or Decimal("0.00")
        )

        if balance < Decimal("0.00"):
            balance = Decimal("0.00")

        return format(balance, ".2f")

    def get_customer_data(self, obj):

        return {

            "id": str(obj.customer.id),

            "customer_code": obj.customer.customer_code,

            "name": obj.customer.name,

            "phone": obj.customer.phone,

            "email": obj.customer.email,

        }
    
    def validate(self, data):
        request = self.context.get("request")

        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError(
                "Tenant not available."
            )

        customer_id = data.get("customer_id")
        customer_data = data.get("customer")
        branch_id = data.get("branch_id")
        items = data.get("items")

        # =====================================================
        # CREATE ONLY VALIDATION
        # =====================================================

        if self.instance is None:

            if not customer_id and not customer_data:
                raise serializers.ValidationError(
                    "Customer is required."
                )

            if not branch_id:
                raise serializers.ValidationError(
                    "Branch is required."
                )

            if not items:
                raise serializers.ValidationError(
                    "Sale must contain at least one item."
                )

        # =====================================================
        # CUSTOMER
        # =====================================================

        if customer_id:

            try:

                data["customer"] = Customer.objects.get(
                    id=customer_id,
                    tenant=request.tenant,
                    is_active=True,
                )

            except Customer.DoesNotExist:

                raise serializers.ValidationError(
                    "Customer not found."
                )

        elif customer_data:

            name = customer_data.get("name", "").strip()

            if not name:

                raise serializers.ValidationError(
                    "Customer name is required."
                )

            customer = Customer.objects.filter(
                tenant=request.tenant,
                name__iexact=name,
                is_active=True,
            ).first()

            if not customer:

                customer = Customer.objects.create(
                    tenant=request.tenant,
                    customer_code=generate_customer_code(request.tenant),
                    name=name,
                    phone=customer_data.get("phone", ""),
                    email=customer_data.get("email", ""),
                    address=customer_data.get("address", ""),
                    created_by=request.user,
                    updated_by=request.user,
                )

            data["customer"] = customer

        # =====================================================
        # BRANCH
        # =====================================================

        if branch_id:

            try:

                data["branch"] = Branch.objects.get(
                    id=branch_id,
                    tenant=request.tenant,
                    is_active=True,
                )

            except Branch.DoesNotExist:

                raise serializers.ValidationError(
                    "Branch not found."
                )

        # =====================================================
        # PRODUCTS
        # =====================================================

        if items:

            product_ids = []

            for item in items:

                product = item.get("product")

                if not product:

                    raise serializers.ValidationError(
                        "Product is required."
                    )

                if product.tenant != request.tenant:

                    raise serializers.ValidationError(
                        f"{product.name} does not belong to this tenant."
                    )

                if not product.is_active:

                    raise serializers.ValidationError(
                        f"{product.name} is inactive."
                    )

                if product.id in product_ids:

                    raise serializers.ValidationError(
                        f"{product.name} appears more than once."
                    )

                product_ids.append(product.id)

                discount_type = item.get(
                    "discount_type",
                    SaleItem.DiscountType.NONE,
                )

                discount_value = item.get(
                    "discount_value",
                    Decimal("0.00"),
                )

                if (
                    discount_type == SaleItem.DiscountType.AMOUNT
                    and discount_value > product.selling_price
                ):
                    raise serializers.ValidationError(
                        {
                            "discount_value":
                            "Discount cannot exceed selling price."
                        }
                    )

                if (
                    discount_type == SaleItem.DiscountType.PERCENTAGE
                    and discount_value > 100
                ):
                    raise serializers.ValidationError(
                        {
                            "discount_value":
                            "Percentage cannot exceed 100."
                        }
                    )

        return data
    
    @transaction.atomic
    def create(self, validated_data):

        items_data = validated_data.pop(
            "items",
            []
        )


        customer = validated_data.pop(
            "customer"
        )


        request = self.context["request"]


        sale = Sale.objects.create(
            customer=customer,
            **validated_data
        )


        total_amount = Decimal(
            "0.00"
        )



        for item_data in items_data:


            product = item_data["product"]

            quantity = item_data["quantity"]


            unit_price = product.selling_price


            discount_type = item_data.get(
                "discount_type",
                SaleItem.DiscountType.NONE
            )


            discount_value = item_data.get(
                "discount_value",
                Decimal("0.00")
            )



            final_price = unit_price



            if discount_type == SaleItem.DiscountType.AMOUNT:

                final_price = (
                    unit_price -
                    discount_value
                )



            elif discount_type == SaleItem.DiscountType.PERCENTAGE:


                final_price = (

                    unit_price -

                    (
                        unit_price *
                        discount_value /
                        Decimal("100")
                    )

                )



            subtotal = (
                quantity *
                final_price
            )


            total_amount += subtotal



            SaleItem.objects.create(

                tenant=request.tenant,

                sale=sale,

                product=product,

                quantity=quantity,

                unit_price=unit_price,

                discount_type=discount_type,

                discount_value=discount_value,

                final_price=final_price,

                subtotal=subtotal,

                created_by=request.user,

                updated_by=request.user,

            )



        sale.total_amount = total_amount


        sale.save(
            update_fields=[
                "total_amount"
            ]
        )


        return sale

    @transaction.atomic
    def update(self, instance, validated_data):

        if instance.status != Sale.DRAFT:
            raise serializers.ValidationError(
                "Cannot update a completed sale."
            )

        request = self.context["request"]

        items_data = validated_data.pop("items", None)
        customer = validated_data.pop("customer", None)
        branch = validated_data.pop("branch", None)

        if customer:
            instance.customer = customer

        if branch:
            instance.branch = branch

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = request.user
        instance.save()

        if items_data is not None:

            for item_data in items_data:

                product = item_data["product"]
                quantity = item_data["quantity"]

                unit_price = product.selling_price

                discount_type = item_data.get(
                    "discount_type",
                    SaleItem.DiscountType.NONE,
                )

                discount_value = item_data.get(
                    "discount_value",
                    Decimal("0.00"),
                )

                final_price = unit_price

                if discount_type == SaleItem.DiscountType.AMOUNT:

                    final_price -= discount_value

                elif discount_type == SaleItem.DiscountType.PERCENTAGE:

                    final_price -= (
                        unit_price * discount_value / Decimal("100")
                    )

                if final_price < 0:

                    raise serializers.ValidationError(
                        "Discount cannot make price negative."
                    )

                subtotal = quantity * final_price

                sale_item = instance.items.filter(
                    tenant=request.tenant,
                    product=product,
                ).first()

                if sale_item:

                    sale_item.quantity = quantity
                    sale_item.unit_price = unit_price
                    sale_item.discount_type = discount_type
                    sale_item.discount_value = discount_value
                    sale_item.final_price = final_price
                    sale_item.subtotal = subtotal
                    sale_item.updated_by = request.user

                    sale_item.save()

                else:

                    SaleItem.objects.create(
                        tenant=request.tenant,
                        sale=instance,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        discount_type=discount_type,
                        discount_value=discount_value,
                        final_price=final_price,
                        subtotal=subtotal,
                        created_by=request.user,
                        updated_by=request.user,
                    )

            instance.total_amount = (
                instance.items.aggregate(
                    total=Sum("subtotal")
                )["total"]
                or Decimal("0.00")
            )

            instance.updated_by = request.user

            instance.save(
                update_fields=[
                    "total_amount",
                    "updated_by",
                ]
            )

        return instance
        