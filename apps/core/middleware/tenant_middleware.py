from apps.core.tenant.models import Tenant
from rest_framework_simplejwt.tokens import AccessToken


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):

        request.tenant = None

        auth_header = request.headers.get(
            "Authorization"
        )


        if auth_header and auth_header.startswith("Bearer "):

            token = auth_header.split(" ")[1]

            try:
                access_token = AccessToken(token)

                tenant_id = access_token.get(
                    "tenant_id"
                )


                if tenant_id:

                    try:
                        request.tenant = Tenant.objects.get(
                            id=tenant_id
                        )

                    except Tenant.DoesNotExist:
                        request.tenant = None


            except Exception:
                request.tenant = None


        response = self.get_response(request)

        return response