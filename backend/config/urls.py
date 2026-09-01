from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_v1_root(request):
    return Response(
        {
            "message": "OTC Exchange API v1",
            "endpoints": {
                "auth": "/api/v1/auth/",
                "assets": "/api/v1/assets/",
                "wallets": "/api/v1/wallets/",
                "otc": "/api/v1/otc/",
                "orders": "/api/v1/orders/",
                "trades": "/api/v1/trades/",
                "transactions": "/api/v1/transactions/",
                "kyc": "/api/v1/kyc/",
                "security": "/api/v1/security/",
                "support": "/api/v1/support/",
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", api_v1_root, name="api-v1-root"),
    path("api/v1/assets/", include("apps.assets.urls")),
    path("api/v1/wallets/", include("apps.wallets.urls")),
    path("api/v1/otc/", include("apps.otc.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/trades/", include("apps.trades.urls")),
    path("api/v1/transactions/", include("apps.transactions.urls")),
    path("api/v1/kyc/", include("apps.kyc.urls")),
    path("api/v1/security/", include("apps.security.urls")),
    path("api/v1/support/", include("apps.support.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
