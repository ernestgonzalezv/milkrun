"""Raiz de composicion.

El unico lugar donde se decide que adaptador concreto satisface cada puerto.
Las vistas piden casos de uso aqui; no construyen dependencias por su cuenta.

Es un modulo con funciones y no un framework de inyeccion: el grafo es lineal
y con doce casos de uso una fabrica explicita se lee mejor que un contenedor
con magia. Si el proyecto creciera a varios contextos, esto se reemplaza sin
tocar ni el dominio ni los adaptadores.
"""

from __future__ import annotations

from functools import cache

from domain.usecases.get_driver_route import GetDriverRoute
from domain.usecases.manage_stops import CreateStop, DeleteStop, GetStop, ListStops, UpdateStop
from domain.usecases.plan_day import PlanDay
from domain.usecases.sync_driver_work import SyncDriverEvents, SyncDriverPings
from domain.usecases.track_shipment import TrackShipment
from infrastructure.clock import DjangoClock
from infrastructure.planner import ClarkeWrightPlanner, HaversineItinerary
from infrastructure.repositories import (
    DjangoEventRepository,
    DjangoFleetRepository,
    DjangoPingRepository,
    DjangoRouteRepository,
    DjangoStopRepository,
    DjangoUnitOfWork,
)


@cache
def _stops() -> DjangoStopRepository:
    return DjangoStopRepository()


@cache
def _routes() -> DjangoRouteRepository:
    return DjangoRouteRepository()


@cache
def _events() -> DjangoEventRepository:
    return DjangoEventRepository()


@cache
def _pings() -> DjangoPingRepository:
    return DjangoPingRepository()


@cache
def _fleet() -> DjangoFleetRepository:
    return DjangoFleetRepository()


@cache
def _uow() -> DjangoUnitOfWork:
    return DjangoUnitOfWork()


@cache
def _clock() -> DjangoClock:
    return DjangoClock()


def clock() -> DjangoClock:
    """El reloj del sistema, para que las vistas no llamen a `timezone.now()`."""
    return _clock()


def plan_day() -> PlanDay:
    return PlanDay(
        fleet=_fleet(),
        stops=_stops(),
        routes=_routes(),
        planner=ClarkeWrightPlanner(),
        itinerary=HaversineItinerary(),
        uow=_uow(),
    )


def sync_driver_events() -> SyncDriverEvents:
    return SyncDriverEvents(events=_events(), stops=_stops(), uow=_uow())


def sync_driver_pings() -> SyncDriverPings:
    return SyncDriverPings(pings=_pings())


def get_driver_route() -> GetDriverRoute:
    return GetDriverRoute(routes=_routes(), clock=_clock())


def track_shipment() -> TrackShipment:
    return TrackShipment(stops=_stops(), events=_events())


def list_stops() -> ListStops:
    return ListStops(stops=_stops())


def get_stop() -> GetStop:
    return GetStop(stops=_stops())


def create_stop() -> CreateStop:
    return CreateStop(stops=_stops())


def update_stop() -> UpdateStop:
    return UpdateStop(stops=_stops())


def delete_stop() -> DeleteStop:
    return DeleteStop(stops=_stops())


def routes_repository() -> DjangoRouteRepository:
    """Las consultas de rutas del despachador no tienen regla de negocio.

    Exponer el repositorio directamente para leer es honesto; envolverlo en un
    caso de uso que solo delega seria ceremonia sin contenido.
    """
    return _routes()


def fleet_repository() -> DjangoFleetRepository:
    return _fleet()
