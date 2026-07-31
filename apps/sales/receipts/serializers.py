from decimal import Decimal

from rest_framework import serializers

from apps.finance.payments.models import Payment
from apps.sales.sales.models import Sale, SaleItem


class ReceiptItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(
        source="final_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = SaleItem
        fields = [
            "product",
            "quantity",
            "price",
            "subtotal",
        ]


class ReceiptPaymentSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "amount",
            "payment_method",
            "date",
        ]


class ReceiptBranchSerializer(serializers.Serializer):
    name = serializers.CharField()
    location = serializers.CharField(allow_blank=True)
    phone = serializers.CharField(source="phone_number", allow_blank=True)


class ReceiptCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True)


class ReceiptSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    branch = ReceiptBranchSerializer(read_only=True)
    customer = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    total = serializers.DecimalField(
        source="total_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    paid = serializers.DecimalField(
        source="paid_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    balance = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "tenant_name",
            "branch",
            "invoice_number",
            "sale_date",
            "customer",
            "items",
            "total",
            "paid",
            "balance",
            "payment_status",
            "payments",
        ]

    def get_customer(self, obj: Sale):
        payload = {
            "id": obj.customer.id,
            "name": obj.customer.name,
            "phone": obj.customer.phone,
        }
        return ReceiptCustomerSerializer(payload).data

    def get_items(self, obj: Sale):
        prefetched = getattr(obj, "_prefetched_objects_cache", {}).get("items")
        if prefetched is not None:
            items_qs = [item for item in prefetched if item.is_active]
        else:
            items_qs = obj.items.filter(is_active=True).select_related("product")
        return ReceiptItemSerializer(items_qs, many=True).data

    def get_balance(self, obj: Sale):
        balance = (obj.total_amount or Decimal("0.00")) - (obj.paid_amount or Decimal("0.00"))
        if balance < Decimal("0.00"):
            return Decimal("0.00")
        return balance

    def get_payments(self, obj: Sale):
        prefetched = getattr(obj, "_prefetched_objects_cache", {}).get("payments")
        if prefetched is not None:
            payments_qs = sorted(
                [payment for payment in prefetched if payment.is_active],
                key=lambda payment: (payment.payment_date, payment.created_at),
            )
        else:
            payments_qs = obj.payments.filter(is_active=True).order_by("payment_date", "created_at")
        return ReceiptPaymentSerializer(payments_qs, many=True).data