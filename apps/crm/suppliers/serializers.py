from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'phone',
            'email',
            'address',
            'contact_person',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                'Supplier name cannot be empty.'
            )

        request = self.context.get('request')

        if not request or not hasattr(request, 'tenant'):
            return value

        tenant = request.tenant
        queryset = Supplier.objects.filter(
            tenant=tenant,
            name__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                'A supplier with this name already exists.'
            )

        return value

