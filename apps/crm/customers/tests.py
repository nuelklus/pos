from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from apps.core.branch.models import Branch
from apps.core.tenant.models import Tenant
from apps.crm.customers.models import Customer
from apps.crm.customers.views import CustomerViewSet
from apps.finance.payments.models import Payment
from apps.sales.sales.models import Sale


class CustomerLedgerResponseContractTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.tenant = Tenant.objects.create(
            name="Tenant A",
            is_active=True,
        )
        self.other_tenant = Tenant.objects.create(
            name="Tenant B",
            is_active=True,
        )

        user_model = get_user_model()
        self.user = user_model.objects.create(
            tenant=self.tenant,
            email="ledger@test.com",
            first_name="Ledger",
            last_name="Tester",
            is_active=True,
        )
        self.other_user = user_model.objects.create(
            tenant=self.other_tenant,
            email="other@test.com",
            first_name="Other",
            last_name="User",
            is_active=True,
        )

        self.branch = Branch.objects.create(
            tenant=self.tenant,
            name="Main Branch",
            is_active=True,
        )
        self.customer = Customer.objects.create(
            tenant=self.tenant,
            customer_code="CUST-000002",
            name="John Mensah",
            phone="0241234567",
            email="john@gmail.com",
            address="Accra",
            is_active=True,
        )

    def _get_ledger_response(self, user, tenant, customer_id):
        request = self.factory.get(f"/api/customers/{customer_id}/ledger/")
        force_authenticate(request, user=user)
        request.tenant = tenant
        view = CustomerViewSet.as_view({"get": "ledger"})
        return view(request, id=str(customer_id))

    def test_ledger_returns_wrapped_contract_with_totals(self):
        sale1 = Sale.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            branch=self.branch,
            invoice_number="INV-000005",
            total_amount=Decimal("5400.00"),
            paid_amount=Decimal("5400.00"),
            status=Sale.COMPLETED,
            payment_status=Sale.PaymentStatus.PAID,
            is_active=True,
        )
        Payment.objects.create(
            tenant=self.tenant,
            sale=sale1,
            amount=Decimal("5400.00"),
            payment_method=Payment.CASH,
            is_active=True,
        )

        sale2 = Sale.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            branch=self.branch,
            invoice_number="INV-000006",
            total_amount=Decimal("26960.00"),
            paid_amount=Decimal("7360.00"),
            status=Sale.COMPLETED,
            payment_status=Sale.PaymentStatus.PARTIAL,
            is_active=True,
        )
        Payment.objects.create(
            tenant=self.tenant,
            sale=sale2,
            amount=Decimal("7360.00"),
            payment_method=Payment.BANK,
            is_active=True,
        )

        response = self._get_ledger_response(self.user, self.tenant, self.customer.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.data
        self.assertIn("customer", payload)
        self.assertIn("entries", payload)
        self.assertIn("total_debit", payload)
        self.assertIn("total_credit", payload)
        self.assertIn("closing_balance", payload)

        customer_payload = payload["customer"]
        self.assertEqual(str(customer_payload["id"]), str(self.customer.id))
        self.assertEqual(customer_payload["customer_code"], "CUST-000002")
        self.assertEqual(customer_payload["name"], "John Mensah")
        self.assertEqual(customer_payload["phone"], "0241234567")
        self.assertEqual(customer_payload["email"], "john@gmail.com")
        self.assertEqual(customer_payload["address"], "Accra")

        entries = payload["entries"]
        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0]["type"], "SALE")
        self.assertEqual(entries[1]["type"], "PAYMENT")

        self.assertEqual(payload["total_debit"], "32360.00")
        self.assertEqual(payload["total_credit"], "12760.00")
        self.assertEqual(payload["closing_balance"], "19600.00")

    def test_ledger_is_tenant_scoped(self):
        response = self._get_ledger_response(self.other_user, self.other_tenant, self.customer.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)