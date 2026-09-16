"""Rutas de la API.

Todo cuelga de /api/v1/ para que agregar una v2 no obligue a tocar los
clientes existentes. El esquema OpenAPI se genera del codigo, no se mantiene a
mano: un contrato escrito aparte se desincroniza en semanas.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    MeView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from apps.deliveries.views import (
    EventSyncView,
    PingSyncView,
    PublicTrackingView,
    StopDetailView,
    StopListView,
)
from apps.fleet.views import DepotViewSet, DriverProfileViewSet, VehicleViewSet
from apps.routing.views import MyRouteView, PlanDayView, RouteDetailView, RouteListView
from apps.shared.health import healthz, readyz

router = DefaultRouter()
router.register("depots", DepotViewSet, basename="depot")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("drivers", DriverProfileViewSet, basename="driver")

api_v1 = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("stops/", StopListView.as_view(), name="stop-list"),
    path("stops/<int:pk>/", StopDetailView.as_view(), name="stop-detail"),
    path("routes/plan/", PlanDayView.as_view(), name="plan-day"),
    path("routes/", RouteListView.as_view(), name="route-list"),
    path("routes/<int:pk>/", RouteDetailView.as_view(), name="route-detail"),
    path("me/route/", MyRouteView.as_view(), name="my-route"),
    path("me/events/", EventSyncView.as_view(), name="event-sync"),
    path("me/pings/", PingSyncView.as_view(), name="ping-sync"),
    path("track/<str:code>/", PublicTrackingView.as_view(), name="public-tracking"),
    *router.urls,
]

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("readyz", readyz, name="readyz"),
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "v1"))),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
