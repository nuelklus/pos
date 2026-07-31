from rest_framework import serializers

from apps.finance.payments.models import Payment
from apps.sales.sales.models import Sale
from apps.crm.customers.models import Customer
from apps.core.users.models import User


class PaymentUserSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
        ]

    def get_name(self, obj):
        name = " ".join(
            filter(
                None,
                [
                    obj.first_name,
                    obj.last_name,
                ]
            )
        )

        return name or obj.email


class PaymentCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
        ]


class PaymentSerializer(serializers.ModelSerializer):

    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(),
        write_only=True,
        source="sale",
    )

    invoice_number = serializers.CharField(
        source="sale.invoice_number",
        read_only=True,
    )

    customer = PaymentCustomerSerializer(
        source="sale.customer",
        read_only=True,
    )

    created_by = PaymentUserSerializer(
        read_only=True,
    )


    class Meta:

        model = Payment

        fields = [
            "id",
            "sale_id",
            "created_by",
            "customer",
            "invoice_number",
            "amount",
            "payment_method",
            "reference",
            "notes",
            "payment_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "payment_date",
            "created_at",
            "updated_at",
        ]


    def validate_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value


    def validate(self, data):

        request = self.context.get("request")

        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError(
                "Tenant not available."
            )


        sale = data.get("sale")

        if not sale:
            raise serializers.ValidationError(
                "Sale is required."
            )


        # Tenant protection
        if sale.tenant != request.tenant:
            raise serializers.ValidationError(
                "Sale does not belong to this tenant."
            )


        # Only completed sales can receive payments
        if sale.status != Sale.COMPLETED:
            raise serializers.ValidationError(
                "Payment can only be added to completed sales."
            )


        amount = data.get("amount")

        balance = (
            sale.total_amount -
            sale.paid_amount
        )


        if amount > balance:
            raise serializers.ValidationError(
                {
                    "amount":
                    f"Payment exceeds outstanding balance. "
                    f"Remaining balance: {balance}"
                }
            )


        return data