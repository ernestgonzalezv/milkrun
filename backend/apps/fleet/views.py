"""Catalogos de flota. Lectura para todo usuario autenticado, escritura solo
para despachadores: un chofer no debe poder cambiar la capacidad de su camion.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from apps.accounts.permissions import IsDispatcher

from .models import Depot, DriverProfile, Vehicle
from .serializers import DepotSerializer, DriverProfileSerializer, VehicleSerializer


class DispatcherWriteMixin:
    def get_permissions(self):
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [IsDispatcher()]
        return super().get_permissions()


@extend_schema(tags=["Fleet"])
class DepotViewSet(DispatcherWriteMixin, viewsets.ModelViewSet):
    queryset = Depot.objects.all()
    serializer_class = DepotSerializer
    filterset_fields = ("is_active",)


@extend_schema(tags=["Fleet"])
class VehicleViewSet(DispatcherWriteMixin, viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("depot")
    serializer_class = VehicleSerializer
    filterset_fields = ("depot", "is_active")


@extend_schema(tags=["Fleet"])
class DriverProfileViewSet(DispatcherWriteMixin, viewsets.ModelViewSet):
    queryset = DriverProfile.objects.select_related("user", "depot", "default_vehicle")
    serializer_class = DriverProfileSerializer
    filterset_fields = ("depot", "is_available")
