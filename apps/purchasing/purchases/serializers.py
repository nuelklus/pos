from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from apps.core.branch.models import Branch
from apps.crm.suppliers.models import Supplier
from apps.inventory.products.models import Product
from .models import Purchase, PurchaseItem


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(write_only=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'product_id',
            'product',
            'quantity',
            'cost_price',
            'subtotal',
        ]
        read_only_fields = ['id', 'subtotal']

    def get_product(self, obj):
        return {
            'id': str(obj.product.id),
            'name': obj.product.name,
            'sku': obj.product.sku,
        }

    def validate_product_id(self, value):
        request = self.context.get('request')
        product = Product.objects.filter(
            tenant=request.tenant,
            id=value,
            is_active=True,
        ).first()

        if not product:
            raise serializers.ValidationError('Invalid product.')

        return value

    def validate(self, attrs):
        if attrs.get('quantity') is None or attrs['quantity'] <= 0:
            raise serializers.ValidationError({'quantity': 'Quantity must be greater than zero.'})
        if attrs.get('cost_price') is None or attrs['cost_price'] < 0:
            raise serializers.ValidationError({'cost_price': 'Cost price must be non-negative.'})
        return attrs

    def create(self, validated_data):
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(
            id=product_id,
            tenant=self.context['request'].tenant,
        )
        subtotal = validated_data['quantity'] * validated_data['cost_price']

        return PurchaseItem.objects.create(
            # tenant=self.context['request'].tenant,
            product=product,
            subtotal=subtotal,
            **validated_data,
        )

    def update(self, instance, validated_data):
        if 'product_id' in validated_data:
            product = Product.objects.get(
                id=validated_data.pop('product_id'),
                tenant=self.context['request'].tenant,
            )
            instance.product = product

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.subtotal = instance.quantity * instance.cost_price
        instance.save()
        return instance


class PurchaseSerializer(serializers.ModelSerializer):
    supplier_id = serializers.UUIDField(write_only=True)
    branch_id = serializers.UUIDField(write_only=True)
    supplier = serializers.SerializerMethodField(read_only=True)
    branch = serializers.SerializerMethodField(read_only=True)
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = Purchase
        fields = [
            'id',
            'supplier_id',
            'supplier',
            'branch_id',
            'branch',
            'invoice_number',
            'purchase_date',
            'status',
            'total_amount',
            'items',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'total_amount', 'is_active', 'created_at', 'updated_at']

    def get_supplier(self, obj):
        return {
            'id': str(obj.supplier.id),
            'name': obj.supplier.name,
        }

    def get_branch(self, obj):
        return {
            'id': str(obj.branch.id),
            'name': obj.branch.name,
        }

    def validate_supplier_id(self, value):
        request = self.context.get('request')
        supplier = Supplier.objects.filter(
            tenant=request.tenant,
            id=value,
            is_active=True,
        ).first()

        if not supplier:
            raise serializers.ValidationError('Invalid supplier.')

        return value

    def validate_branch_id(self, value):
        request = self.context.get('request')
        branch = Branch.objects.filter(
            tenant=request.tenant,
            id=value,
            is_active=True,
        ).first()

        if not branch:
            raise serializers.ValidationError('Invalid branch.')

        return value

    def validate_invoice_number(self, value):
        value = value.strip()
        request = self.context.get('request')
        queryset = Purchase.objects.filter(
            tenant=request.tenant,
            invoice_number__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError('A purchase with this invoice number already exists.')

        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Purchase must include at least one item.')
        return value

    def validate(self, attrs):
        if self.instance and self.instance.status == Purchase.Status.RECEIVED:
            raise serializers.ValidationError('Received purchases cannot be modified.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        supplier_id = validated_data.pop('supplier_id')
        branch_id = validated_data.pop('branch_id')

        supplier = Supplier.objects.get(
            id=supplier_id,
            tenant=self.context['request'].tenant,
        )
        branch = Branch.objects.get(
            id=branch_id,
            tenant=self.context['request'].tenant,
        )

        purchase = Purchase.objects.create(
            supplier=supplier,
            branch=branch,
            # tenant=self.context['request'].tenant,
            **validated_data,
        )

        total_amount = Decimal('0')

        for item_data in items_data:
            item_data['tenant'] = purchase.tenant
            item_data['purchase'] = purchase
            item = PurchaseItemSerializer(context=self.context).create(item_data)
            total_amount += item.subtotal

        purchase.total_amount = total_amount
        purchase.save(update_fields=['total_amount'])

        return purchase

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        supplier_id = validated_data.pop('supplier_id', None)
        branch_id = validated_data.pop('branch_id', None)

        if supplier_id:
            instance.supplier = Supplier.objects.get(
                id=supplier_id,
                tenant=self.context['request'].tenant,
            )

        if branch_id:
            instance.branch = Branch.objects.get(
                id=branch_id,
                tenant=self.context['request'].tenant,
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            total_amount = 0
            for item_data in items_data:
                item_data['tenant'] = instance.tenant
                item_data['purchase'] = instance
                item = PurchaseItemSerializer(context=self.context).create(item_data)
                total_amount += item.subtotal
            instance.total_amount = total_amount
            instance.save(update_fields=['total_amount'])

        return instance

