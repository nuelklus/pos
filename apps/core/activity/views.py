from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.core.activity.models import ActivityLog
from apps.core.activity.serializers import ActivityLogSerializer
from apps.core.permissions.permissions import IsTenantUser


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    lookup_field = "id"
    lookup_value_regex = "[0-9a-f-]{36}"

    class ActivityPagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = "page_size"
        max_page_size = 100

    pagination_class = ActivityPagination

    def get_queryset(self):
        if not getattr(self.request, "tenant", None):
            return ActivityLog.objects.none()

        return ActivityLog.objects.filter(
            tenant=self.request.tenant,
            is_active=True,
        ).select_related("user").order_by("-created_at")
