from rest_framework import serializers

from .models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    branch = serializers.SerializerMethodField(read_only=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'branch',
            'product',
            'movement_type',
            'quantity',
            'reference_type',
            'reference_id',
            'created_at',
        ]
        read_only_fields = ['id', 'branch', 'product', 'created_at']

    def get_branch(self, obj):
        return {
            'id': str(obj.branch.id),
            'name': obj.branch.name,
        }

    def get_product(self, obj):
        return {
            'id': str(obj.product.id),
            'name': obj.product.name,
            'sku': obj.product.sku,
        }

