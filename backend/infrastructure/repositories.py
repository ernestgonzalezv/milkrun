"""Repositorios sobre el ORM de Django.

Cumplen los `Protocol` de `domain/ports.py` sin heredar de ellos. Toda consulta
al ORM del proyecto vive aqui o en el admin; ninguna vista arma un queryset.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import date
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch

from apps.deliveries.models import DeliveryEvent as EventModel
from apps.deliveries.models import LocationPing as PingModel
from apps.deliveries.models import Stop as StopModel
from apps.fleet.models import Depot as DepotModel
from apps.fleet.models import DriverProfile as DriverProfileModel
from apps.fleet.models import Vehicle as VehicleModel
from apps.routing.models import Route as RouteModel
from apps.routing.models import RouteStop as RouteStopModel
from domain.entities import DeliveryEvent, Depot, Driver, LocationPing, Route, Stop, Vehicle
from domain.ports import Page, RouteFilters, StopFilters
from domain.values import RouteStatus, StopStatus

from .mappers import (
    depot_to_entity,
    driver_to_entity,
    event_to_entity,
    route_to_entity,
    stop_to_entity,
    stop_to_model_fields,
    vehicle_to_entity,
)


class DjangoUnitOfWork:
    def atomic(self):
        return transaction.atomic()


class DjangoFleetRepository:
    def get_depot(self, depot_id: int, *, only_active: bool = False) -> Depot | None:
        query = DepotModel.objects.filter(pk=depot_id)
        if only_active:
            query = query.filter(is_active=True)
        model = query.first()
        return depot_to_entity(model) if model else None

    def list_depots(self, *, is_active: bool | None = None) -> tuple[Depot, ...]:
        query = DepotModel.objects.all()
        if is_active is not None:
            query = query.filter(is_active=is_active)
        return tuple(depot_to_entity(m) for m in query)

    def active_vehicles(self, depot_id: int) -> tuple[Vehicle, ...]:
        return tuple(
            vehicle_to_entity(m)
            for m in VehicleModel.objects.filter(depot_id=depot_id, is_active=True).order_by("code")
        )

    def available_drivers(self, depot_id: int) -> tuple[Driver, ...]:
        return tuple(
            driver_to_entity(m)
            for m in DriverProfileModel.objects.filter(
                depot_id=depot_id, is_available=True, user__is_active=True
            )
            .select_related("user", "default_vehicle")
            .order_by("user__username")
        )


class DjangoStopRepository:
    def get(self, stop_id: int) -> Stop | None:
        model = StopModel.objects.filter(pk=stop_id).first()
        return stop_to_entity(model) if model else None

    def get_by_tracking_code(self, code: str) -> Stop | None:
        model = StopModel.objects.filter(tracking_code=code).first()
        return stop_to_entity(model) if model else None

    def list(self, filters: StopFilters) -> Page[Stop]:
        query = StopModel.objects.all()
        if filters.depot_id is not None:
            query = query.filter(depot_id=filters.depot_id)
        if filters.scheduled_date is not None:
            query = query.filter(scheduled_date=filters.scheduled_date)
        if filters.status is not None:
            query = query.filter(status=filters.status)

        total = query.count()
        window = query.order_by("scheduled_date", "created_at")[
            filters.offset : filters.offset + filters.limit
        ]
        return Page(items=tuple(stop_to_entity(m) for m in window), total=total)

    def plannable(self, depot_id: int, day: date) -> tuple[Stop, ...]:
        planificables = (StopStatus.PENDING, StopStatus.PLANNED)
        return tuple(
            stop_to_entity(m)
            for m in StopModel.objects.filter(
                depot_id=depot_id, scheduled_date=day, status__in=planificables
            ).order_by("created_at", "id")
        )

    def add(self, stop: Stop) -> Stop:
        model = StopModel.objects.create(
            tracking_code=stop.tracking_code, **stop_to_model_fields(stop)
        )
        return stop_to_entity(model)

    def replace(self, stop: Stop) -> Stop:
        StopModel.objects.filter(pk=stop.id).update(**stop_to_model_fields(stop))
        return self.get(stop.id)

    def delete(self, stop_id: int) -> None:
        StopModel.objects.filter(pk=stop_id).delete()

    def set_status(self, stop_ids: Sequence[int], status: StopStatus) -> None:
        if stop_ids:
            StopModel.objects.filter(pk__in=list(stop_ids)).update(status=status)

    def ids_assigned_to_driver(self, driver_id: int) -> frozenset[int]:
        return frozenset(
            StopModel.objects.filter(route_stops__route__driver_id=driver_id).values_list(
                "id", flat=True
            )
        )

    def is_planned(self, stop_id: int) -> bool:
        return RouteStopModel.objects.filter(stop_id=stop_id).exists()


class DjangoEventRepository:
    def append(self, event: DeliveryEvent) -> DeliveryEvent | None:
        """La idempotencia la da la restriccion unica, no una lectura previa.

        Comprobar con un `exists()` antes del insert deja una ventana de
        carrera entre la lectura y la escritura; la restriccion no.
        """
        try:
            with transaction.atomic():
                model = EventModel.objects.create(
                    stop_id=event.stop_id,
                    driver_id=event.driver_id,
                    client_event_id=event.client_event_id,
                    kind=event.kind,
                    reason=event.reason or "",
                    note=event.note,
                    latitude=event.coordinates.latitude if event.coordinates else None,
                    longitude=event.coordinates.longitude if event.coordinates else None,
                    occurred_at=event.occurred_at,
                )
        except IntegrityError:
            return None
        return event_to_entity(model)

    def for_stop(self, stop_id: int) -> tuple[DeliveryEvent, ...]:
        return tuple(
            event_to_entity(m)
            for m in EventModel.objects.filter(stop_id=stop_id).order_by("occurred_at", "id")
        )

    def exists(self, driver_id: int, client_event_id: UUID) -> bool:
        return EventModel.objects.filter(
            driver_id=driver_id, client_event_id=client_event_id
        ).exists()


class DjangoPingRepository:
    def append_many(self, pings: Sequence[LocationPing]) -> int:
        """Filtra reenvios por marca de tiempo y deja la restriccion como red.

        Lo primero da un conteo exacto para devolver al cliente; lo segundo
        cubre la carrera entre dos peticiones simultaneas del mismo telefono.
        No se puede contar por `pk` sobre el resultado de `bulk_create`, porque
        con `ignore_conflicts` varios backends devuelven objetos sin clave.
        """
        if not pings:
            return 0

        driver_id = pings[0].driver_id
        marks = [p.recorded_at for p in pings]
        already = set(
            PingModel.objects.filter(driver_id=driver_id, recorded_at__in=marks).values_list(
                "recorded_at", flat=True
            )
        )

        seen: set = set()
        fresh = []
        for ping in pings:
            if ping.recorded_at in already or ping.recorded_at in seen:
                continue
            seen.add(ping.recorded_at)
            fresh.append(
                PingModel(
                    driver_id=ping.driver_id,
                    latitude=ping.coordinates.latitude,
                    longitude=ping.coordinates.longitude,
                    accuracy_m=ping.accuracy_m,
                    speed_kmh=ping.speed_kmh,
                    recorded_at=ping.recorded_at,
                )
            )

        PingModel.objects.bulk_create(fresh, ignore_conflicts=True, batch_size=500)
        return len(fresh)


class DjangoRouteRepository:
    def get(self, route_id: int) -> Route | None:
        model = self._detailed().filter(pk=route_id).first()
        return route_to_entity(model, with_stops=True) if model else None

    def list(self, filters: RouteFilters) -> Page[Route]:
        query = self._detailed() if filters.with_stops else self._summary()
        if filters.depot_id is not None:
            query = query.filter(depot_id=filters.depot_id)
        if filters.date is not None:
            query = query.filter(date=filters.date)
        if filters.status is not None:
            query = query.filter(status=filters.status)
        if filters.driver_id is not None:
            query = query.filter(driver_id=filters.driver_id)

        total = query.count()
        window = query[filters.offset : filters.offset + filters.limit]
        return Page(
            items=tuple(route_to_entity(m, with_stops=filters.with_stops) for m in window),
            total=total,
        )

    def for_driver(self, driver_id: int, day: date) -> Route | None:
        model = self._detailed().filter(driver_id=driver_id, date=day).first()
        return route_to_entity(model, with_stops=True) if model else None

    def statuses_for(self, depot_id: int, day: date) -> tuple[RouteStatus, ...]:
        return tuple(
            RouteStatus(s)
            for s in RouteModel.objects.filter(depot_id=depot_id, date=day).values_list(
                "status", flat=True
            )
        )

    def delete_for(self, depot_id: int, day: date) -> None:
        RouteModel.objects.filter(depot_id=depot_id, date=day).delete()

    def add_many(self, routes: Sequence[Route]) -> tuple[Route, ...]:
        stored = []
        for route in routes:
            model = RouteModel.objects.create(
                depot_id=route.depot_id,
                vehicle_id=route.vehicle_id,
                driver_id=route.driver_id,
                date=route.date,
                status=route.status,
                planned_distance_km=route.planned_distance_km,
                planned_duration_minutes=route.planned_duration_minutes,
                planned_load=route.planned_load,
                optimizer_metrics=route.optimizer_metrics,
            )
            RouteStopModel.objects.bulk_create(
                RouteStopModel(
                    route=model,
                    stop_id=rs.stop_id,
                    sequence=rs.sequence,
                    leg_distance_km=rs.leg_distance_km,
                    eta_minutes=rs.eta_minutes,
                )
                for rs in route.stops
            )
            stored.append(model.id)

        return tuple(
            route_to_entity(m, with_stops=True) for m in self._detailed().filter(pk__in=stored)
        )

    def iter_for(self, depot_id: int, day: date) -> Iterator[Route]:
        for model in self._detailed().filter(depot_id=depot_id, date=day):
            yield route_to_entity(model, with_stops=True)

    @staticmethod
    def _summary():
        return (
            RouteModel.objects.select_related("depot", "vehicle", "driver")
            .annotate(stop_count=Count("route_stops"))
            .order_by("-date", "vehicle__code")
        )

    @staticmethod
    def _detailed():
        """Un solo sitio define como se carga una ruta completa.

        Sin el prefetch, serializar 5 rutas de 20 paradas dispara ~100
        consultas. Con el son 4.
        """
        return (
            RouteModel.objects.select_related("depot", "vehicle", "driver")
            .prefetch_related(
                Prefetch(
                    "route_stops",
                    queryset=RouteStopModel.objects.select_related("stop").order_by("sequence"),
                )
            )
            .order_by("-date", "vehicle__code")
        )
