import json
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.core.activity.views import ActivityLogViewSet
from apps.core.dashboard.views import InventoryDashboardViewSet, OwnerDashboardViewSet
from apps.crm.customers.models import Customer
from apps.crm.customers.views import CustomerViewSet
from apps.sales.sales.models import Sale
from apps.sales.sales.views import SaleViewSet


class Command(BaseCommand):
    help = "Benchmark hot API endpoints (latency + DB query count) and save a reusable JSON snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            default="",
            help="User email to benchmark as. Defaults to first active user.",
        )
        parser.add_argument(
            "--tenant-id",
            type=str,
            default="",
            help="Optional tenant UUID. Defaults to the selected user's tenant.",
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=5,
            help="Number of timed iterations per endpoint.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="benchmark_results/hot_endpoints_latest.json",
            help="Output path for benchmark snapshot JSON (absolute or relative to project root).",
        )
        parser.add_argument(
            "--include-raw",
            action="store_true",
            help="Include per-iteration raw timing and query arrays in output.",
        )

    def handle(self, *args, **options):
        iterations = max(1, int(options["iterations"]))
        include_raw = bool(options["include_raw"])

        user = self._select_user(options["user_email"])
        tenant = self._select_tenant(user, options["tenant_id"])
        self._validate_user_tenant(user, tenant)

        endpoint_specs = self._build_endpoint_specs(tenant=tenant)
        if not endpoint_specs:
            raise CommandError("No benchmark endpoints available.")

        factory = APIRequestFactory()
        results = []
        for spec in endpoint_specs:
            result = self._benchmark_endpoint(
                factory=factory,
                user=user,
                tenant=tenant,
                iterations=iterations,
                include_raw=include_raw,
                spec=spec,
            )
            results.append(result)

        output_payload = {
            "generated_at": timezone.now().isoformat(),
            "project_root": str(settings.BASE_DIR),
            "user_email": user.email,
            "tenant_id": str(tenant.id),
            "iterations": iterations,
            "endpoints": results,
        }
        output_file = self._write_output(
            payload=output_payload,
            output_path=options["output"],
        )

        self.stdout.write(self.style.SUCCESS(f"Benchmark snapshot saved: {output_file}"))
        for row in results:
            status = row["status"]
            avg_ms = row.get("avg_ms")
            avg_queries = row.get("avg_queries")
            self.stdout.write(
                f"- {row['name']}: status={status}, avg_ms={avg_ms}, avg_queries={avg_queries}"
            )

    def _select_user(self, user_email):
        user_model = get_user_model()
        if user_email:
            user = user_model.objects.filter(
                email=user_email,
                is_active=True,
            ).first()
            if not user:
                raise CommandError(f"Active user not found for email: {user_email}")
            return user

        user = user_model.objects.filter(is_active=True).order_by("date_joined").first()
        if not user:
            raise CommandError("No active users found.")
        return user

    def _select_tenant(self, user, tenant_id):
        if tenant_id:
            from apps.core.tenant.models import Tenant

            tenant = Tenant.objects.filter(
                id=tenant_id,
                is_active=True,
            ).first()
            if not tenant:
                raise CommandError(f"Active tenant not found: {tenant_id}")
            return tenant

        if not getattr(user, "tenant", None):
            raise CommandError("Selected user has no tenant.")
        return user.tenant

    def _validate_user_tenant(self, user, tenant):
        if getattr(user, "tenant_id", None) != tenant.id:
            raise CommandError(
                "Selected user does not belong to selected tenant. "
                "Pass a user/tenant pair from the same tenant."
            )

    def _build_endpoint_specs(self, tenant):
        sale = Sale.objects.filter(
            tenant=tenant,
            is_active=True,
            status=Sale.COMPLETED,
        ).order_by("-sale_date").first()
        customer = Customer.objects.filter(
            tenant=tenant,
            is_active=True,
        ).order_by("-created_at").first()

        specs = [
            {
                "name": "owner_dashboard",
                "method": "get",
                "path": "/api/dashboard/",
                "view": OwnerDashboardViewSet.as_view({"get": "list"}),
                "kwargs": {},
            },
            {
                "name": "inventory_dashboard",
                "method": "get",
                "path": "/api/inventory/dashboard/",
                "view": InventoryDashboardViewSet.as_view({"get": "list"}),
                "kwargs": {},
            },
            {
                "name": "activity_list",
                "method": "get",
                "path": "/api/activity/",
                "view": ActivityLogViewSet.as_view({"get": "list"}),
                "kwargs": {},
            },
            {
                "name": "customers_accounts_dashboard",
                "method": "get",
                "path": "/api/customers/accounts/dashboard/",
                "view": CustomerViewSet.as_view({"get": "accounts_dashboard"}),
                "kwargs": {},
            },
        ]

        if customer:
            specs.append(
                {
                    "name": "customer_ledger",
                    "method": "get",
                    "path": f"/api/customers/{customer.id}/ledger/",
                    "view": CustomerViewSet.as_view({"get": "ledger"}),
                    "kwargs": {"id": str(customer.id)},
                }
            )

        if sale:
            specs.append(
                {
                    "name": "sales_receipt",
                    "method": "get",
                    "path": f"/api/sales/{sale.id}/receipt/",
                    "view": SaleViewSet.as_view({"get": "receipt"}),
                    "kwargs": {"id": str(sale.id)},
                }
            )

        return specs

    def _benchmark_endpoint(
        self,
        *,
        factory,
        user,
        tenant,
        iterations,
        include_raw,
        spec,
    ):
        timings_ms = []
        query_counts = []
        status_code = None
        error_text = ""

        for _ in range(iterations):
            request = self._make_request(
                factory=factory,
                method=spec["method"],
                path=spec["path"],
                user=user,
                tenant=tenant,
            )
            try:
                with CaptureQueriesContext(connection) as ctx:
                    start = perf_counter()
                    response = spec["view"](request, **spec["kwargs"])
                    if hasattr(response, "render"):
                        response.render()
                    elapsed_ms = (perf_counter() - start) * 1000

                timings_ms.append(round(elapsed_ms, 3))
                query_counts.append(len(ctx.captured_queries))
                status_code = response.status_code
                if status_code >= 400:
                    error_text = f"HTTP {status_code}"
                    break
            except Exception as exc:
                error_text = str(exc)
                break

        output = {
            "name": spec["name"],
            "method": spec["method"].upper(),
            "path": spec["path"],
            "status": status_code if status_code is not None else "error",
            "iterations_completed": len(timings_ms),
            "avg_ms": round(sum(timings_ms) / len(timings_ms), 3) if timings_ms else None,
            "min_ms": min(timings_ms) if timings_ms else None,
            "max_ms": max(timings_ms) if timings_ms else None,
            "avg_queries": round(sum(query_counts) / len(query_counts), 2) if query_counts else None,
            "min_queries": min(query_counts) if query_counts else None,
            "max_queries": max(query_counts) if query_counts else None,
        }
        if error_text:
            output["error"] = error_text
        if include_raw:
            output["raw_timings_ms"] = timings_ms
            output["raw_query_counts"] = query_counts
        return output

    def _make_request(self, *, factory, method, path, user, tenant):
        request = getattr(factory, method.lower())(path)
        force_authenticate(request, user=user)
        request.tenant = tenant
        return request

    def _write_output(self, *, payload, output_path):
        output = Path(output_path)
        if not output.is_absolute():
            output = Path(settings.BASE_DIR) / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(output)
