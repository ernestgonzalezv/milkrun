"""Traduccion entre modelos de Django y entidades del dominio.

Es la frontera: por encima de esta linea hay entidades inmutables, por debajo
filas de una base relacional. Vive en un solo archivo para que cambiar el
esquema tenga un unico sitio que revisar.
"""

from __future__ import annotations

from apps.deliveries.models import DeliveryEvent as EventModel
from apps.deliveries.models import Stop as StopModel
from apps.fleet.models import Depot as DepotModel
from apps.fleet.models import DriverProfile as DriverProfileModel
from apps.fleet.models import Vehicle as VehicleModel
from apps.routing.models import Route as RouteModel
from apps.routing.models import RouteStop as RouteStopModel
from domain.entities import DeliveryEvent, Depot, Driver, Route, RouteStop, Stop, Vehicle
from domain.values import Coordinates, EventKind, FailureReason, RouteStatus, StopStatus


def depot_to_entity(model: DepotModel) -> Depot:
    return Depot(
        id=model.id,
        name=model.name,
        address=model.address,
        coordinates=Coordinates(model.latitude, model.longitude),
        is_active=model.is_active,
    )


def vehicle_to_entity(model: VehicleModel) -> Vehicle:
    return Vehicle(
        id=model.id,
        depot_id=model.depot_id,
        code=model.code,
        capacity=model.capacity,
        max_shift_minutes=model.max_shift_minutes,
        avg_speed_kmh=model.avg_speed_kmh,
        plate=model.plate,
        is_active=model.is_active,
    )


def driver_to_entity(model: DriverProfileModel) -> Driver:
    return Driver(
        id=model.user_id,
        username=model.user.username,
        full_name=model.user.get_full_name(),
        depot_id=model.depot_id,
        default_vehicle_id=model.default_vehicle_id,
        is_available=model.is_available,
    )


def stop_to_entity(model: StopModel) -> Stop:
    return Stop(
        id=model.id,
        tracking_code=model.tracking_code,
        depot_id=model.depot_id,
        customer_name=model.customer_name,
        address=model.address,
        coordinates=Coordinates(model.latitude, model.longitude),
        scheduled_date=model.scheduled_date,
        demand=model.demand,
        service_minutes=model.service_minutes,
        status=StopStatus(model.status),
        phone=model.phone,
        notes=model.notes,
        created_at=model.created_at,
    )


def stop_to_model_fields(stop: Stop) -> dict:
    return {
        "depot_id": stop.depot_id,
        "customer_name": stop.customer_name,
        "address": stop.address,
        "latitude": stop.coordinates.latitude,
        "longitude": stop.coordinates.longitude,
        "demand": stop.demand,
        "service_minutes": stop.service_minutes,
        "scheduled_date": stop.scheduled_date,
        "phone": stop.phone,
        "notes": stop.notes,
    }


def event_to_entity(model: EventModel) -> DeliveryEvent:
    coordinates = (
        Coordinates(model.latitude, model.longitude)
        if model.latitude is not None and model.longitude is not None
        else None
    )
    return DeliveryEvent(
        id=model.id,
        stop_id=model.stop_id,
        driver_id=model.driver_id,
        client_event_id=model.client_event_id,
        kind=EventKind(model.kind),
        occurred_at=model.occurred_at,
        reason=FailureReason(model.reason) if model.reason else None,
        note=model.note,
        coordinates=coordinates,
        received_at=model.received_at,
    )


def route_stop_to_entity(model: RouteStopModel, *, with_stop: bool = False) -> RouteStop:
    return RouteStop(
        stop_id=model.stop_id,
        sequence=model.sequence,
        leg_distance_km=model.leg_distance_km,
        eta_minutes=model.eta_minutes,
        stop=stop_to_entity(model.stop) if with_stop else None,
    )


def route_to_entity(model: RouteModel, *, with_stops: bool = False) -> Route:
    stops: tuple[RouteStop, ...] = ()
    if with_stops:
        stops = tuple(
            route_stop_to_entity(rs, with_stop=True) for rs in model.route_stops.all()
        )
    # `stop_count` viene anotado en el listado liviano y de las paradas en el detalle.
    stop_count = len(stops) if with_stops else getattr(model, "stop_count", 0)

    return Route(
        id=model.id,
        depot_id=model.depot_id,
        vehicle_id=model.vehicle_id,
        date=model.date,
        driver_id=model.driver_id,
        status=RouteStatus(model.status),
        planned_distance_km=model.planned_distance_km,
        planned_duration_minutes=model.planned_duration_minutes,
        planned_load=model.planned_load,
        optimizer_metrics=model.optimizer_metrics,
        stops=stops,
        vehicle_code=model.vehicle.code if model.vehicle_id else "",
        driver_name=model.driver.get_full_name() if model.driver_id else "",
        stop_count=stop_count,
    )
