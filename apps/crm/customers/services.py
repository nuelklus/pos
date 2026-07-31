from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.crm.customers.models import Customer
from apps.finance.payments.models import Payment
from apps.sales.sales.models import Sale

ZERO = Decimal("0.00")


def generate_customer_code(tenant):
    last_customer = Customer.objects.filter(
        tenant=tenant,
        # is_active=True,
    ).order_by("-created_at").first()

    if not last_customer or not last_customer.customer_code:
        number = 1
    else:
        try:
            code_parts = last_customer.customer_code.split("-")
            if len(code_parts) == 2:
                number = int(code_parts[1]) + 1
            else:
                number = 1
        except (ValueError, IndexError):
            number = 1

    return f"CUST-{number:06d}"


def get_customer_or_404(*, tenant, customer_id) -> Customer:
    customer = Customer.objects.filter(
        tenant=tenant,
        is_active=True,
        id=customer_id,
    ).only(
        "id",
        "customer_code",
        "name",
        "phone",
        "email",
        "address",
    ).first()
    if not customer:
        raise NotFound("Customer not found.")
    return customer


def _completed_sales_queryset(*, tenant, customer: Customer):
    return Sale.objects.filter(
        tenant=tenant,
        customer=customer,
        is_active=True,
        status=Sale.COMPLETED,
    )


def _balance_expression():
    return ExpressionWrapper(
        F("total_amount") - F("paid_amount"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


def get_customer_account_summary(*, tenant, customer_id) -> dict[str, Any]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    sales_qs = _completed_sales_queryset(tenant=tenant, customer=customer)

    totals = sales_qs.aggregate(
        total_sales=Coalesce(
            Sum("total_amount"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        total_paid=Coalesce(
            Sum("paid_amount"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        credit_sales=Count(
            "id",
            filter=Q(
                payment_status__in=[
                    Sale.PaymentStatus.UNPAID,
                    Sale.PaymentStatus.PARTIAL,
                ]
            ),
        ),
    )

    last_payment = Payment.objects.filter(
        tenant=tenant,
        is_active=True,
        sale__tenant=tenant,
        sale__is_active=True,
        sale__status=Sale.COMPLETED,
        sale__customer=customer,
    ).order_by("-payment_date").values_list("payment_date", flat=True).first()

    total_sales = totals["total_sales"] or ZERO
    total_paid = totals["total_paid"] or ZERO
    outstanding_balance = total_sales - total_paid

    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        },
        "total_sales": total_sales,
        "total_paid": total_paid,
        "outstanding_balance": outstanding_balance,
        "credit_sales": totals["credit_sales"] or 0,
        "last_payment": last_payment,
    }


def get_customer_statement(*, tenant, customer_id) -> list[dict[str, Any]]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    sales_qs = _completed_sales_queryset(
        tenant=tenant,
        customer=customer,
    ).annotate(balance=_balance_expression()).order_by("sale_date", "created_at")

    return list(
        sales_qs.values(
            "invoice_number",
            "sale_date",
            "total_amount",
            "paid_amount",
            "balance",
            "payment_status",
        )
    )


def get_customer_outstanding_invoices(*, tenant, customer_id) -> list[dict[str, Any]]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    sales_qs = _completed_sales_queryset(
        tenant=tenant,
        customer=customer,
    ).filter(
        payment_status__in=[
            Sale.PaymentStatus.UNPAID,
            Sale.PaymentStatus.PARTIAL,
        ]
    ).annotate(balance=_balance_expression()).order_by("sale_date", "created_at")

    return list(
        sales_qs.values(
            "invoice_number",
            "sale_date",
            "total_amount",
            "paid_amount",
            "balance",
            "payment_status",
        )
    )


def get_customer_payment_history(*, tenant, customer_id) -> list[dict[str, Any]]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    payment_qs = Payment.objects.filter(
        tenant=tenant,
        is_active=True,
        sale__tenant=tenant,
        sale__is_active=True,
        sale__status=Sale.COMPLETED,
        sale__customer=customer,
    ).select_related("sale").order_by("-payment_date", "-created_at")

    return list(
        payment_qs.values(
            "sale__invoice_number",
            "amount",
            "payment_method",
            "reference",
            "payment_date",
        )
    )


def get_customer_aging(*, tenant, customer_id) -> dict[str, Decimal]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    sales_qs = _completed_sales_queryset(
        tenant=tenant,
        customer=customer,
    ).filter(
        payment_status__in=[
            Sale.PaymentStatus.UNPAID,
            Sale.PaymentStatus.PARTIAL,
        ]
    ).values("sale_date", "total_amount", "paid_amount")

    today = timezone.now().date()
    buckets = {
        "current": ZERO,
        "1_30": ZERO,
        "31_60": ZERO,
        "61_90": ZERO,
        "90_plus": ZERO,
    }

    for sale in sales_qs:
        balance = (sale["total_amount"] or ZERO) - (sale["paid_amount"] or ZERO)
        if balance <= ZERO:
            continue

        age_days = max((today - sale["sale_date"].date()).days, 0)
        if age_days == 0:
            buckets["current"] += balance
        elif age_days <= 30:
            buckets["1_30"] += balance
        elif age_days <= 60:
            buckets["31_60"] += balance
        elif age_days <= 90:
            buckets["61_90"] += balance
        else:
            buckets["90_plus"] += balance

    return buckets


def get_customer_ledger(*, tenant, customer_id) -> dict[str, Any]:
    customer = get_customer_or_404(tenant=tenant, customer_id=customer_id)
    sales = _completed_sales_queryset(
        tenant=tenant,
        customer=customer,
    ).values(
        "invoice_number",
        "sale_date",
        "total_amount",
    )
    payments = Payment.objects.filter(
        tenant=tenant,
        is_active=True,
        sale__tenant=tenant,
        sale__is_active=True,
        sale__status=Sale.COMPLETED,
        sale__customer=customer,
    ).select_related("sale").values(
        "sale__invoice_number",
        "payment_date",
        "amount",
    )

    ledger_entries: list[dict[str, Any]] = []
    for sale in sales:
        ledger_entries.append(
            {
                "type": "SALE",
                "invoice": sale["invoice_number"],
                "transaction_date": sale["sale_date"],
                "debit": sale["total_amount"] or ZERO,
                "credit": ZERO,
            }
        )

    for payment in payments:
        ledger_entries.append(
            {
                "type": "PAYMENT",
                "invoice": payment["sale__invoice_number"],
                "transaction_date": payment["payment_date"],
                "debit": ZERO,
                "credit": payment["amount"] or ZERO,
            }
        )

    ledger_entries.sort(
        key=lambda entry: (
            entry["transaction_date"],
            0 if entry["type"] == "SALE" else 1,
        )
    )

    running_balance = ZERO
    for entry in ledger_entries:
        running_balance += entry["debit"] - entry["credit"]
        entry["balance"] = running_balance

    total_debit = sum((entry["debit"] for entry in ledger_entries), ZERO)
    total_credit = sum((entry["credit"] for entry in ledger_entries), ZERO)
    closing_balance = ledger_entries[-1]["balance"] if ledger_entries else ZERO

    return {
        "customer": {
            "id": customer.id,
            "customer_code": customer.customer_code,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "address": customer.address,
        },
        "entries": ledger_entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "closing_balance": closing_balance,
    }


def get_dashboard_receivables(*, tenant) -> dict[str, Any]:
    completed_sales_qs = Sale.objects.filter(
        tenant=tenant,
        is_active=True,
        status=Sale.COMPLETED,
    )
    outstanding_sales_qs = completed_sales_qs.filter(
        payment_status__in=[
            Sale.PaymentStatus.UNPAID,
            Sale.PaymentStatus.PARTIAL,
        ]
    ).annotate(balance=_balance_expression())

    customers_with_credit = outstanding_sales_qs.values("customer_id").distinct().count()
    total_receivables = outstanding_sales_qs.aggregate(
        total=Coalesce(
            Sum("balance"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["total"] or ZERO

    overdue_cutoff = timezone.now() - timedelta(days=30)
    overdue_receivables = outstanding_sales_qs.filter(
        sale_date__lt=overdue_cutoff,
    ).aggregate(
        total=Coalesce(
            Sum("balance"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["total"] or ZERO

    customer_outstanding = completed_sales_qs.values("customer_id").annotate(
        outstanding=Coalesce(
            Sum(_balance_expression()),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )
    fully_paid_customers = customer_outstanding.filter(outstanding__lte=ZERO).count()

    return {
        "customers_with_credit": customers_with_credit,
        "total_receivables": total_receivables,
        "overdue_receivables": overdue_receivables,
        "fully_paid_customers": fully_paid_customers,
    }
