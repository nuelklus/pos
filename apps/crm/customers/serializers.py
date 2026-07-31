from rest_framework import serializers

from apps.crm.customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_code',
            'name',
            'phone',
            'email',
            'address',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'customer_code',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                'Customer name cannot be empty.'
            )

        request = self.context.get('request')

        if not request or not hasattr(request, 'tenant'):
            return value

        tenant = request.tenant
        queryset = Customer.objects.filter(
            tenant=tenant,
            name__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                'A customer with this name already exists.'
            )

        return value


class CustomerAccountCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True)


class CustomerAccountSerializer(serializers.Serializer):
    customer = CustomerAccountCustomerSerializer()
    total_sales = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_sales = serializers.IntegerField()
    last_payment = serializers.DateTimeField(allow_null=True)


class CustomerStatementSerializer(serializers.Serializer):
    invoice_number = serializers.CharField()
    sale_date = serializers.DateTimeField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    payment_status = serializers.CharField()


class OutstandingInvoiceSerializer(serializers.Serializer):
    invoice_number = serializers.CharField()
    sale_date = serializers.DateTimeField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    payment_status = serializers.CharField()


class CustomerPaymentHistorySerializer(serializers.Serializer):
    invoice_number = serializers.CharField(source="sale__invoice_number")
    payment_amount = serializers.DecimalField(source="amount", max_digits=14, decimal_places=2)
    payment_method = serializers.CharField()
    reference = serializers.CharField(allow_blank=True)
    payment_date = serializers.DateTimeField()


class CustomerAgingSerializer(serializers.Serializer):
    current = serializers.DecimalField(max_digits=14, decimal_places=2)
    one_to_thirty = serializers.DecimalField(source="1_30", max_digits=14, decimal_places=2)
    thirty_one_to_sixty = serializers.DecimalField(source="31_60", max_digits=14, decimal_places=2)
    sixty_one_to_ninety = serializers.DecimalField(source="61_90", max_digits=14, decimal_places=2)
    ninety_plus = serializers.DecimalField(source="90_plus", max_digits=14, decimal_places=2)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            "current": data["current"],
            "1_30": data["one_to_thirty"],
            "31_60": data["thirty_one_to_sixty"],
            "61_90": data["sixty_one_to_ninety"],
            "90_plus": data["ninety_plus"],
        }


class CustomerLedgerSerializer(serializers.Serializer):
    type = serializers.CharField()
    invoice = serializers.CharField()
    transaction_date = serializers.DateTimeField()
    debit = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class CustomerLedgerCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    customer_code = serializers.CharField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    address = serializers.CharField(allow_blank=True)


class CustomerLedgerResponseSerializer(serializers.Serializer):
    customer = CustomerLedgerCustomerSerializer()
    entries = CustomerLedgerSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=14, decimal_places=2)
    closing_balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardReceivableSerializer(serializers.Serializer):
    customers_with_credit = serializers.IntegerField()
    total_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_receivables = serializers.DecimalField(max_digits=14, decimal_places=2)
    fully_paid_customers = serializers.IntegerField()
