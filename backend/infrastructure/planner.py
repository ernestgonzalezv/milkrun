"""Adaptador del optimizador.

Traduce entidades del dominio a los tipos del paquete `optimizer` y de vuelta.
Es el unico sitio donde se nombra la heuristica concreta: cambiarla por
OR-Tools es escribir otro adaptador con esta misma forma. Ver docs/adr/0001.
"""

from __future__ import annotations

from collections.abc import Sequence

from domain.entities import Depot, Stop, Vehicle
from domain.ports import PlannedRoute, PlanResult
from optimizer import Fleet, Point, solve
from optimizer import Stop as OptimizerStop
from optimizer import Vehicle as OptimizerVehicle
from optimizer.itinerary import legs as compute_legs


class ClarkeWrightPlanner:
    def plan(
        self,
        depot: Depot,
        vehicles: Sequence[Vehicle],
        stops: Sequence[Stop],
    ) -> PlanResult:
        fleet = Fleet(
            depot=_point(depot),
            vehicles=tuple(
                OptimizerVehicle(
                    id=str(vehicle.id),
                    capacity=vehicle.capacity,
                    max_shift_minutes=float(vehicle.max_shift_minutes),
                    avg_speed_kmh=vehicle.avg_speed_kmh,
                )
                for vehicle in vehicles
            ),
        )
        instance = tuple(
            OptimizerStop(
                id=str(stop.id),
                point=_point(stop),
                demand=stop.demand,
                service_minutes=float(stop.service_minutes),
            )
            for stop in stops
        )

        plan = solve(fleet, instance)

        return PlanResult(
            routes=tuple(
                PlannedRoute(
                    vehicle_id=int(route.vehicle_id),
                    stop_ids=tuple(int(sid) for sid in route.stop_ids),
                    distance_km=route.distance_km,
                    load=route.load,
                    duration_minutes=route.duration_minutes,
                )
                for route in plan.routes
            ),
            unassigned_stop_ids=tuple(int(sid) for sid in plan.unassigned),
            metrics=plan.metrics,
        )


class HaversineItinerary:
    def legs(
        self,
        depot: Depot,
        stops: Sequence[Stop],
        speed_kmh: float,
    ) -> tuple[tuple[float, float], ...]:
        computed = compute_legs(
            depot=_point(depot),
            points=[_point(stop) for stop in stops],
            service_minutes=[float(stop.service_minutes) for stop in stops],
            speed_kmh=speed_kmh,
        )
        return tuple((leg.distance_km, leg.eta_minutes) for leg in computed)


def _point(located) -> Point:
    return Point(located.coordinates.latitude, located.coordinates.longitude)
