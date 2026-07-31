from rest_framework import serializers

from apps.core.activity.models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "action",
            "module",
            "description",
            "reference_id",
            "user",
            "user_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        if not obj.user:
            return ""
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.email
