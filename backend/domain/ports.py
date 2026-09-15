"""Puertos: lo que el dominio necesita del mundo exterior.

Son `Protocol`, no clases base: los adaptadores no heredan de nada, solo
cumplen la forma. Asi el dominio no aparece como dependencia en la firma de
`infrastructure/`, y la direccion de las dependencias queda de una sola via.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from .entities import DeliveryEvent, Depot, Driver, LocationPing, Route, Stop, Vehicle
from .values import RouteStatus, StopStatus


@dataclass(frozen=True, slots=True)
class Page[T]:
    """Un tramo de resultados y cuantos hay en total."""

    items: tuple[T, ...]
    total: int


@dataclass(frozen=True, slots=True)
class StopFilters:
    depot_id: int | None = None
    scheduled_date: date | None = None
    status: StopStatus | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class RouteFilters:
    depot_id: int | None = None
    date: date | None = None
    status: RouteStatus | None = None
    driver_id: int | None = None
    with_stops: bool = False
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class PlannedRoute:
    """Salida del planificador, todavia sin persistir."""

    vehicle_id: int
    stop_ids: tuple[int, ...]
    distance_km: float
    load: float
    duration_minutes: float


@dataclass(frozen=True, slots=True)
class PlanResult:
    routes: tuple[PlannedRoute, ...]
    unassigned_stop_ids: tuple[int, ...]
    metrics: dict = field(default_factory=dict)


class RoutePlanner(Protocol):
    """Quien decide que paradas van juntas y en que orden.

    Es un puerto y no una llamada directa al paquete `optimizer` para que
    cambiar de heuristica —a OR-Tools, por ejemplo— sea escribir otro
    adaptador y no tocar el caso de uso. Ver docs/adr/0001.
    """

    def plan(
        self,
        depot: Depot,
        vehicles: Sequence[Vehicle],
        stops: Sequence[Stop],
    ) -> PlanResult: ...


class Itinerary(Protocol):
    """Desglose tramo a tramo de una ruta ya ordenada."""

    def legs(
        self,
        depot: Depot,
        stops: Sequence[Stop],
        speed_kmh: float,
    ) -> Sequence[tuple[float, float]]:
        """Devuelve (km del tramo, ETA acumulado en minutos) por parada."""
        ...


class UnitOfWork(Protocol):
    """Frontera transaccional. El caso de uso decide que es atomico."""

    def atomic(self) -> AbstractContextManager[None]: ...


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class FleetRepository(Protocol):
    def get_depot(self, depot_id: int, *, only_active: bool = False) -> Depot | None: ...

    def list_depots(self, *, is_active: bool | None = None) -> tuple[Depot, ...]: ...

    def active_vehicles(self, depot_id: int) -> tuple[Vehicle, ...]: ...

    def available_drivers(self, depot_id: int) -> tuple[Driver, ...]: ...


class StopRepository(Protocol):
    def get(self, stop_id: int) -> Stop | None: ...

    def get_by_tracking_code(self, code: str) -> Stop | None: ...

    def list(self, filters: StopFilters) -> Page[Stop]: ...

    def plannable(self, depot_id: int, day: date) -> tuple[Stop, ...]: ...

    def add(self, stop: Stop) -> Stop: ...

    def replace(self, stop: Stop) -> Stop: ...

    def delete(self, stop_id: int) -> None: ...

    def set_status(self, stop_ids: Sequence[int], status: StopStatus) -> None: ...

    def ids_assigned_to_driver(self, driver_id: int) -> frozenset[int]: ...

    def is_planned(self, stop_id: int) -> bool: ...


class EventRepository(Protocol):
    def append(self, event: DeliveryEvent) -> DeliveryEvent | None:
        """Devuelve `None` si el evento ya estaba (reenvio de la cola offline)."""
        ...

    def for_stop(self, stop_id: int) -> tuple[DeliveryEvent, ...]: ...

    def exists(self, driver_id: int, client_event_id: UUID) -> bool: ...


class PingRepository(Protocol):
    def append_many(self, pings: Sequence[LocationPing]) -> int:
        """Devuelve cuantas posiciones eran nuevas."""
        ...


class RouteRepository(Protocol):
    def get(self, route_id: int) -> Route | None: ...

    def list(self, filters: RouteFilters) -> Page[Route]: ...

    def for_driver(self, driver_id: int, day: date) -> Route | None: ...

    def statuses_for(self, depot_id: int, day: date) -> tuple[RouteStatus, ...]: ...

    def delete_for(self, depot_id: int, day: date) -> None: ...

    def add_many(self, routes: Sequence[Route]) -> tuple[Route, ...]: ...

    def iter_for(self, depot_id: int, day: date) -> Iterator[Route]: ...
