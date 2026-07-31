from rest_framework import serializers

from rest_framework import serializers


class RecentSaleSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    invoice_number = serializers.CharField()

    customer_name = serializers.CharField()

    cashier = serializers.CharField(
        allow_null=True
    )

    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    paid_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_status = serializers.CharField()

    sale_date = serializers.DateTimeField()

class OwnerDashboardSerializer(serializers.Serializer):
    today_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    today_transactions = serializers.IntegerField()
    total_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    customers_owing = serializers.IntegerField()
    total_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_customers = serializers.IntegerField()
    completed_sales = serializers.IntegerField()
    draft_sales = serializers.IntegerField()
    recent_sales = RecentSaleSerializer(
        many=True
    )

class InventoryDashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_stock_quantity = serializers.DecimalField(max_digits=14, decimal_places=2)
    low_stock_items = serializers.IntegerField()
    out_of_stock_items = serializers.IntegerField()
    active_products = serializers.IntegerField()
    low_stock_products = serializers.ListField()
    out_of_stock_products = serializers.ListField()
