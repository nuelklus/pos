from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError
from rest_framework import serializers
from apps.core.activity.services import log_activity
from apps.crm.customers.models import Customer
from apps.crm.customers.permissions import HasTenantContext
from apps.crm.customers.serializers import (
    CustomerAccountSerializer,
    CustomerAgingSerializer,
    CustomerLedgerResponseSerializer,
    CustomerPaymentHistorySerializer,
    CustomerSerializer,
    CustomerStatementSerializer,
    DashboardReceivableSerializer,
    OutstandingInvoiceSerializer,
)
from apps.crm.customers.services import (
    generate_customer_code,
    get_customer_account_summary,
    get_customer_aging,
    get_customer_ledger,
    get_customer_outstanding_invoices,
    get_customer_payment_history,
    get_customer_statement,
    get_dashboard_receivables,
)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasTenantContext]
    lookup_field = "id"
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        if not self.request.tenant:
            return Customer.objects.none()

        return Customer.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).order_by("name")

    def perform_create(self, serializer):
        try:
            customer_code = generate_customer_code(self.request.tenant)

            customer = serializer.save(
                tenant=self.request.tenant,
                customer_code=customer_code,
                created_by=self.request.user,
                updated_by=self.request.user,
            )

            log_activity(
                tenant=self.request.tenant,
                user=self.request.user,
                action="CREATED",
                module="CUSTOMER",
                description=f"Created customer {customer.name}.",
                reference_id=customer.id,
            )

        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "detail": "We could not complete this customer registration due to a reference number conflict. Please try again."
                }
            )
    def perform_update(self, serializer):
        customer = serializer.save(
            updated_by=self.request.user,
        )
        log_activity(
            tenant=self.request.tenant,
            user=self.request.user,
            action="UPDATED",
            module="CUSTOMER",
            description=f"Updated customer {customer.name}.",
            reference_id=customer.id,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save()

    @action(detail=True, methods=["get"], url_path="account")
    def account(self, request, id=None):
        payload = get_customer_account_summary(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = CustomerAccountSerializer(payload)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="statement")
    def statement(self, request, id=None):
        payload = get_customer_statement(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = CustomerStatementSerializer(payload, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="outstanding")
    def outstanding(self, request, id=None):
        payload = get_customer_outstanding_invoices(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = OutstandingInvoiceSerializer(payload, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="payments")
    def payments(self, request, id=None):
        payload = get_customer_payment_history(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = CustomerPaymentHistorySerializer(payload, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="aging")
    def aging(self, request, id=None):
        payload = get_customer_aging(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = CustomerAgingSerializer(payload)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="ledger")
    def ledger(self, request, id=None):
        payload = get_customer_ledger(
            tenant=request.tenant,
            customer_id=id,
        )
        serializer = CustomerLedgerResponseSerializer(payload)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="accounts/dashboard")
    def accounts_dashboard(self, request):
        payload = get_dashboard_receivables(tenant=request.tenant)
        serializer = DashboardReceivableSerializer(payload)
        return Response(serializer.data)
