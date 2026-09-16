"""Planificar el reparto de un deposito para un dia."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from ..entities import Driver, Route, RouteStop, Stop, Vehicle
from ..errors import PlanningError
from ..ports import (
    FleetRepository,
    Itinerary,
    PlannedRoute,
    RoutePlanner,
    RouteRepository,
    StopRepository,
    UnitOfWork,
)
from ..values import RouteStatus, StopStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PlanDayResult:
    routes: tuple[Route, ...]
    unassigned: tuple[Stop, ...]
    metrics: dict


class PlanDay:
    def __init__(
        self,
        fleet: FleetRepository,
        stops: StopRepository,
        routes: RouteRepository,
        planner: RoutePlanner,
        itinerary: Itinerary,
        uow: UnitOfWork,
    ) -> None:
        self._fleet = fleet
        self._stops = stops
        self._routes = routes
        self._planner = planner
        self._itinerary = itinerary
        self._uow = uow

    def __call__(self, depot_id: int, day: date, *, replan: bool = False) -> PlanDayResult:
        """Calcula y persiste las rutas del dia.

        Todo ocurre dentro de una transaccion: o queda el plan completo o no
        queda nada. Un plan a medias es peor que ninguno, porque el
        despachador no tiene forma de saber que falta.
        """
        depot = self._fleet.get_depot(depot_id, only_active=True)
        if depot is None:
            raise PlanningError("El deposito no existe o no esta activo.")

        vehicles = self._fleet.active_vehicles(depot_id)
        if not vehicles:
            raise PlanningError(f"El deposito {depot.name} no tiene vehiculos activos.")

        pending = self._stops.plannable(depot_id, day)
        if not pending:
            raise PlanningError(f"No hay paradas pendientes para el {day:%d/%m/%Y}.")

        with self._uow.atomic():
            self._clear_previous_plan(depot_id, day, replan=replan)

            plan = self._planner.plan(depot, vehicles, pending)
            by_id = {stop.id: stop for stop in pending}
            vehicles_by_id = {vehicle.id: vehicle for vehicle in vehicles}
            drivers = list(self._fleet.available_drivers(depot_id))

            drafts = [
                self._build_route(
                    depot,
                    vehicles_by_id[planned.vehicle_id],
                    planned,
                    by_id,
                    drivers,
                    index,
                    day,
                    plan.metrics,
                )
                for index, planned in enumerate(plan.routes)
            ]
            stored = self._routes.add_many(drafts)

            served = [sid for planned in plan.routes for sid in planned.stop_ids]
            self._stops.set_status(served, StopStatus.PLANNED)
            self._stops.set_status(plan.unassigned_stop_ids, StopStatus.PENDING)

        unassigned = tuple(by_id[sid] for sid in plan.unassigned_stop_ids)
        logger.info(
            "plan %s %s: %d rutas, %d paradas, %.1f km (%.1f%% mejor que el ruteo manual)",
            depot.name,
            day,
            len(stored),
            len(served),
            sum(r.planned_distance_km for r in stored),
            plan.metrics.get("improvement_vs_nearest_neighbor_pct", 0.0),
        )
        return PlanDayResult(routes=stored, unassigned=unassigned, metrics=plan.metrics)

    def _clear_previous_plan(self, depot_id: int, day: date, *, replan: bool) -> None:
        statuses = self._routes.statuses_for(depot_id, day)
        if not statuses:
            return
        if not replan:
            raise PlanningError(
                f"Ya hay un plan para el {day:%d/%m/%Y}. Reenvia con replan=true para rehacerlo."
            )
        if any(not status.is_replannable for status in statuses):
            raise PlanningError("No se puede replanificar: hay rutas ya en curso o completadas.")
        self._routes.delete_for(depot_id, day)

    def _build_route(
        self,
        depot,
        vehicle: Vehicle,
        planned: PlannedRoute,
        by_id: dict[int, Stop],
        drivers: list[Driver],
        index: int,
        day: date,
        metrics: dict,
    ) -> Route:
        ordered = [by_id[sid] for sid in planned.stop_ids]
        legs = self._itinerary.legs(depot, ordered, vehicle.avg_speed_kmh)

        return Route(
            id=None,
            depot_id=depot.id,
            vehicle_id=vehicle.id,
            date=day,
            driver_id=self._pick_driver(drivers, vehicle, index),
            status=RouteStatus.DRAFT,
            planned_distance_km=round(planned.distance_km, 3),
            planned_duration_minutes=round(planned.duration_minutes, 1),
            planned_load=planned.load,
            optimizer_metrics=metrics,
            stops=tuple(
                RouteStop(
                    stop_id=stop.id,
                    sequence=position + 1,
                    leg_distance_km=legs[position][0],
                    eta_minutes=legs[position][1],
                )
                for position, stop in enumerate(ordered)
            ),
        )

    @staticmethod
    def _pick_driver(pool: list[Driver], vehicle: Vehicle, index: int) -> int | None:
        """Prefiere al chofer habitual del vehiculo; si no hay, reparte por orden.

        Deliberadamente simple: emparejar chofer y vehiculo de forma optima es
        otro problema de asignacion, y hoy el negocio no lo pide.
        """
        for driver in pool:
            if driver.default_vehicle_id == vehicle.id:
                pool.remove(driver)
                return driver.id
        if index < len(pool):
            return pool.pop(0).id
        return None
