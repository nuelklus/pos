from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.crm.customers.models import Customer
from apps.inventory.products.models import Product
from apps.sales.sales.models import Sale

ZERO = Decimal("0.00")


def _balance_expression():
    return ExpressionWrapper(
        F("total_amount") - F("paid_amount"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


def get_owner_dashboard_data(*, tenant):
    now = timezone.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    completed_sales_qs = Sale.objects.filter(
        tenant=tenant,
        is_active=True,
        status=Sale.COMPLETED,
    )
    today_completed_qs = completed_sales_qs.filter(
        sale_date__gte=day_start,
        sale_date__lt=day_end,
    )

    today_sales = today_completed_qs.aggregate(
        total=Coalesce(
            Sum("total_amount"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["total"] or ZERO
    today_transactions = today_completed_qs.count()

    product_qs = Product.objects.filter(
        tenant=tenant,
        is_active=True,
    )
    total_products = product_qs.count()
    low_stock_products = product_qs.filter(
        minimum_stock__gt=ZERO,
        current_stock__lte=F("minimum_stock"),
    ).count()

    customer_qs = Customer.objects.filter(
        tenant=tenant,
        is_active=True,
    )
    total_customers = customer_qs.count()

    outstanding_sales_qs = completed_sales_qs.filter(
        payment_status__in=[
            Sale.PaymentStatus.UNPAID,
            Sale.PaymentStatus.PARTIAL,
        ]
    ).annotate(balance=_balance_expression())

    customers_owing = outstanding_sales_qs.values("customer_id").distinct().count()
    total_receivables = outstanding_sales_qs.aggregate(
        total=Coalesce(
            Sum("balance"),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["total"] or ZERO

    sale_status_counts = Sale.objects.filter(
        tenant=tenant,
        is_active=True,
    ).aggregate(
        completed_sales=Count("id", filter=Q(status=Sale.COMPLETED)),
        draft_sales=Count("id", filter=Q(status=Sale.DRAFT)),
    )
    
    recent_sales = (
        completed_sales_qs
        .select_related("customer", "created_by")
        .order_by("-sale_date")[:5]
    )

    recent_sales_data = [
        {
            "id": sale.id,
            "invoice_number": sale.invoice_number,
            "customer_name": sale.customer.name,
            "cashier": (
                sale.created_by.get_full_name()
                if sale.created_by and hasattr(sale.created_by, "get_full_name")
                else (
                    sale.created_by.email
                    if sale.created_by
                    else None
                )
            ),
            "total_amount": sale.total_amount,
            "paid_amount": sale.paid_amount,
            "balance": sale.total_amount - sale.paid_amount,
            "payment_status": sale.payment_status,
            "sale_date": sale.sale_date,
        }
        for sale in recent_sales
    ]

    return {
        "today_sales": today_sales,
        "today_transactions": today_transactions,
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "customers_owing": customers_owing,
        "total_receivables": total_receivables,
        "total_customers": total_customers,
        "completed_sales": sale_status_counts["completed_sales"] or 0,
        "draft_sales": sale_status_counts["draft_sales"] or 0,
        "recent_sales": recent_sales_data,
    }


def get_inventory_dashboard_data(*, tenant):
    all_products_qs = Product.objects.filter(tenant=tenant)
    stock_value_expr = ExpressionWrapper(
        F("current_stock") * F("cost_price"),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    stock_totals = all_products_qs.aggregate(
        total_products=Count("id"),
        active_products=Count("id", filter=Q(is_active=True)),
        low_stock_items=Count(
            "id",
            filter=Q(
                is_active=True,
                minimum_stock__gt=ZERO,
                current_stock__gt=ZERO,
                current_stock__lte=F("minimum_stock"),
            ),
        ),
        out_of_stock_items=Count(
            "id",
            filter=Q(
                is_active=True,
                current_stock__lte=ZERO,
            ),
        ),
        total_stock_value=Coalesce(
            Sum(stock_value_expr, filter=Q(is_active=True)),
            Value(ZERO),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        ),
        total_stock_quantity=Coalesce(
            Sum("current_stock", filter=Q(is_active=True)),
            Value(ZERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )

    # Get actual low stock products
    low_stock_products = Product.objects.filter(
        tenant=tenant,
        is_active=True,
        minimum_stock__gt=ZERO,
        current_stock__gt=ZERO,
        current_stock__lte=F("minimum_stock"),
    ).values(
        "id",
        "name",
        "sku",
        "current_stock",
        "minimum_stock",
    )
    # Get actual out of stock products
    out_of_stock_products = Product.objects.filter(
        tenant=tenant,
        is_active=True,
        current_stock__lte=ZERO,
    ).values(
        "id",
        "name",
        "sku",
        "current_stock",
    )
    return {
        "total_products": stock_totals["total_products"] or 0,
        "total_stock_value": stock_totals["total_stock_value"] or ZERO,
        "total_stock_quantity": stock_totals["total_stock_quantity"] or ZERO,
        "low_stock_items": stock_totals["low_stock_items"] or 0,
        "out_of_stock_items": stock_totals["out_of_stock_items"] or 0,
        "active_products": stock_totals["active_products"] or 0,
        "low_stock_products": list(low_stock_products),
        "out_of_stock_products": list(out_of_stock_products),
    }
