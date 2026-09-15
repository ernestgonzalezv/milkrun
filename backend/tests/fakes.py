"""Adaptadores en memoria de los puertos del dominio.

Existen para que los casos de uso se puedan probar sin Django ni base de
datos. Que esto sea posible es la razon de tener puertos: si un test de
negocio necesitara migraciones aplicadas, la inversion de dependencias no
estaria haciendo su trabajo.
"""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

from domain.entities import DeliveryEvent, Depot, Driver, LocationPing, Route, Stop, Vehicle
from domain.ports import Page, PlannedRoute, PlanResult, RouteFilters, StopFilters
from domain.values import RouteStatus, StopStatus


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.entered = 0

    @contextlib.contextmanager
    def atomic(self):
        self.entered += 1
        yield


class FakeClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def today(self) -> date:
        return self._moment.date()

    def now(self) -> datetime:
        return self._moment


class FakeFleetRepository:
    def __init__(
        self,
        depots: Sequence[Depot] = (),
        vehicles: Sequence[Vehicle] = (),
        drivers: Sequence[Driver] = (),
    ) -> None:
        self._depots = list(depots)
        self._vehicles = list(vehicles)
        self._drivers = list(drivers)

    def get_depot(self, depot_id: int, *, only_active: bool = False) -> Depot | None:
        for depot in self._depots:
            if depot.id == depot_id and (not only_active or depot.is_active):
                return depot
        return None

    def list_depots(self, *, is_active: bool | None = None) -> tuple[Depot, ...]:
        return tuple(d for d in self._depots if is_active is None or d.is_active == is_active)

    def active_vehicles(self, depot_id: int) -> tuple[Vehicle, ...]:
        return tuple(v for v in self._vehicles if v.depot_id == depot_id and v.is_active)

    def available_drivers(self, depot_id: int) -> tuple[Driver, ...]:
        return tuple(d for d in self._drivers if d.depot_id == depot_id and d.is_available)


class FakeStopRepository:
    def __init__(self, stops: Sequence[Stop] = ()) -> None:
        self.stops = {s.id: s for s in stops}
        self.planned_ids: set[int] = set()
        self.assigned: dict[int, set[int]] = {}

    def get(self, stop_id: int) -> Stop | None:
        return self.stops.get(stop_id)

    def get_by_tracking_code(self, code: str) -> Stop | None:
        return next((s for s in self.stops.values() if s.tracking_code == code), None)

    def list(self, filters: StopFilters) -> Page[Stop]:
        items = [
            s
            for s in self.stops.values()
            if (filters.depot_id is None or s.depot_id == filters.depot_id)
            and (filters.status is None or s.status is filters.status)
        ]
        window = items[filters.offset : filters.offset + filters.limit]
        return Page(items=tuple(window), total=len(items))

    def plannable(self, depot_id: int, day: date) -> tuple[Stop, ...]:
        return tuple(
            s
            for s in self.stops.values()
            if s.depot_id == depot_id
            and s.scheduled_date == day
            and s.status in (StopStatus.PENDING, StopStatus.PLANNED)
        )

    def add(self, stop: Stop) -> Stop:
        from dataclasses import replace

        stored = replace(stop, id=max(self.stops, default=0) + 1)
        self.stops[stored.id] = stored
        return stored

    def replace(self, stop: Stop) -> Stop:
        self.stops[stop.id] = stop
        return stop

    def delete(self, stop_id: int) -> None:
        self.stops.pop(stop_id, None)

    def set_status(self, stop_ids: Sequence[int], status: StopStatus) -> None:
        from dataclasses import replace

        for stop_id in stop_ids:
            if stop_id in self.stops:
                self.stops[stop_id] = replace(self.stops[stop_id], status=status)

    def ids_assigned_to_driver(self, driver_id: int) -> frozenset[int]:
        return frozenset(self.assigned.get(driver_id, set()))

    def is_planned(self, stop_id: int) -> bool:
        return stop_id in self.planned_ids


class FakeEventRepository:
    def __init__(self) -> None:
        self.events: list[DeliveryEvent] = []

    def append(self, event: DeliveryEvent) -> DeliveryEvent | None:
        if self.exists(event.driver_id, event.client_event_id):
            return None
        from dataclasses import replace

        stored = replace(event, id=len(self.events) + 1)
        self.events.append(stored)
        return stored

    def for_stop(self, stop_id: int) -> tuple[DeliveryEvent, ...]:
        return tuple(e for e in self.events if e.stop_id == stop_id)

    def exists(self, driver_id: int, client_event_id: UUID) -> bool:
        return any(
            e.driver_id == driver_id and e.client_event_id == client_event_id for e in self.events
        )


class FakePingRepository:
    def __init__(self) -> None:
        self.pings: list[LocationPing] = []

    def append_many(self, pings: Sequence[LocationPing]) -> int:
        seen = {(p.driver_id, p.recorded_at) for p in self.pings}
        fresh = [p for p in pings if (p.driver_id, p.recorded_at) not in seen]
        self.pings.extend(fresh)
        return len(fresh)


class FakeRouteRepository:
    def __init__(self, routes: Sequence[Route] = ()) -> None:
        self.routes = list(routes)
        self.deleted_days: list[tuple[int, date]] = []

    def get(self, route_id: int) -> Route | None:
        return next((r for r in self.routes if r.id == route_id), None)

    def list(self, filters: RouteFilters) -> Page[Route]:
        items = [r for r in self.routes if filters.date is None or r.date == filters.date]
        return Page(items=tuple(items), total=len(items))

    def for_driver(self, driver_id: int, day: date) -> Route | None:
        return next(
            (r for r in self.routes if r.driver_id == driver_id and r.date == day), None
        )

    def statuses_for(self, depot_id: int, day: date) -> tuple[RouteStatus, ...]:
        return tuple(r.status for r in self.routes if r.depot_id == depot_id and r.date == day)

    def delete_for(self, depot_id: int, day: date) -> None:
        self.deleted_days.append((depot_id, day))
        self.routes = [r for r in self.routes if not (r.depot_id == depot_id and r.date == day)]

    def add_many(self, routes: Sequence[Route]) -> tuple[Route, ...]:
        from dataclasses import replace

        stored = tuple(
            replace(route, id=len(self.routes) + index + 1) for index, route in enumerate(routes)
        )
        self.routes.extend(stored)
        return stored

    def iter_for(self, depot_id: int, day: date):
        yield from (r for r in self.routes if r.depot_id == depot_id and r.date == day)


class FakePlanner:
    """Planificador de guion: devuelve lo que el test le diga."""

    def __init__(self, result: PlanResult) -> None:
        self.result = result
        self.calls = 0

    def plan(self, depot, vehicles, stops) -> PlanResult:
        self.calls += 1
        return self.result


class FakeItinerary:
    def legs(self, depot, stops, speed_kmh):
        return tuple((1.5, (index + 1) * 10.0) for index in range(len(stops)))


def planned(vehicle_id: int, *stop_ids: int) -> PlannedRoute:
    return PlannedRoute(
        vehicle_id=vehicle_id,
        stop_ids=stop_ids,
        distance_km=12.5,
        load=float(len(stop_ids)),
        duration_minutes=90.0,
    )
