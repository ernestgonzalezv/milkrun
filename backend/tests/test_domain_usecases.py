"""Casos de uso contra puertos falsos.

Ninguno de estos tests toca la base de datos ni levanta Django: corren en
milisegundos. Que eso sea posible es lo que demuestra que la inversion de
dependencias esta hecha de verdad y no solo declarada.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from domain.entities import DeliveryEvent, Depot, Driver, LocationPing, Route, Stop, Vehicle
from domain.errors import PlanningError, StopNotAssignedToDriverError, StopNotFoundError
from domain.ports import PlanResult
from domain.usecases.get_driver_route import GetDriverRoute
from domain.usecases.plan_day import PlanDay
from domain.usecases.sync_driver_work import SyncDriverEvents, SyncDriverPings
from domain.usecases.track_shipment import TrackShipment
from domain.values import Coordinates, EventKind, FailureReason, RouteStatus, StopStatus

from .fakes import (
    FakeClock,
    FakeEventRepository,
    FakeFleetRepository,
    FakeItinerary,
    FakePingRepository,
    FakePlanner,
    FakeRouteRepository,
    FakeStopRepository,
    FakeUnitOfWork,
    planned,
)

HOY = date(2026, 9, 12)
AHORA = datetime(2026, 9, 12, 14, 0)
DEPOT = Depot(
    id=1,
    name="Almacen Central",
    address="Boyeros",
    coordinates=Coordinates(23.05, -82.38),
)


def vehiculo(vehicle_id: int) -> Vehicle:
    return Vehicle(id=vehicle_id, depot_id=1, code=f"CAM-{vehicle_id:02d}", capacity=55.0)


def parada(stop_id: int, status: StopStatus = StopStatus.PENDING) -> Stop:
    return Stop(
        id=stop_id,
        tracking_code=f"CODE{stop_id:04d}",
        depot_id=1,
        customer_name=f"Cliente {stop_id} Apellido",
        address=f"Calle {stop_id}",
        coordinates=Coordinates(23.1 + stop_id / 1000, -82.3),
        scheduled_date=HOY,
        status=status,
    )


class TestPlanificarElDia:
    def _caso(self, *, stops, vehicles=(1, 2), routes=(), plan_result=None, drivers=()):
        self.stops = FakeStopRepository(stops)
        self.routes = FakeRouteRepository(routes)
        self.uow = FakeUnitOfWork()
        self.planner = FakePlanner(
            plan_result
            or PlanResult(
                routes=(planned(1, *[s.id for s in stops]),),
                unassigned_stop_ids=(),
                metrics={"total_km": 12.5},
            )
        )
        return PlanDay(
            fleet=FakeFleetRepository(
                depots=[DEPOT], vehicles=[vehiculo(v) for v in vehicles], drivers=list(drivers)
            ),
            stops=self.stops,
            routes=self.routes,
            planner=self.planner,
            itinerary=FakeItinerary(),
            uow=self.uow,
        )

    def test_persiste_las_rutas_y_marca_las_paradas_como_planificadas(self):
        plan_day = self._caso(stops=[parada(1), parada(2)])

        resultado = plan_day(depot_id=1, day=HOY)

        assert len(resultado.routes) == 1
        assert resultado.routes[0].stops[0].sequence == 1
        assert all(s.status is StopStatus.PLANNED for s in self.stops.stops.values())

    def test_todo_ocurre_dentro_de_una_transaccion(self):
        plan_day = self._caso(stops=[parada(1)])

        plan_day(depot_id=1, day=HOY)

        assert self.uow.entered == 1

    def test_un_deposito_inexistente_es_un_error_de_negocio(self):
        plan_day = self._caso(stops=[parada(1)])

        with pytest.raises(PlanningError, match="deposito"):
            plan_day(depot_id=99, day=HOY)

    def test_sin_vehiculos_activos_no_se_planifica(self):
        plan_day = self._caso(stops=[parada(1)], vehicles=())

        with pytest.raises(PlanningError, match="vehiculos activos"):
            plan_day(depot_id=1, day=HOY)

    def test_sin_paradas_pendientes_no_se_planifica(self):
        plan_day = self._caso(stops=[])

        with pytest.raises(PlanningError, match="No hay paradas"):
            plan_day(depot_id=1, day=HOY)

    def test_replanificar_sin_pedirlo_se_rechaza(self):
        existente = Route(id=1, depot_id=1, vehicle_id=1, date=HOY, status=RouteStatus.DRAFT)
        plan_day = self._caso(stops=[parada(1)], routes=[existente])

        with pytest.raises(PlanningError, match="replan=true"):
            plan_day(depot_id=1, day=HOY)

    def test_replanificar_con_el_flag_borra_el_plan_anterior(self):
        existente = Route(id=1, depot_id=1, vehicle_id=1, date=HOY, status=RouteStatus.DRAFT)
        plan_day = self._caso(stops=[parada(1)], routes=[existente])

        plan_day(depot_id=1, day=HOY, replan=True)

        assert self.routes.deleted_days == [(1, HOY)]

    def test_no_se_replanifica_un_dia_que_ya_arranco(self):
        en_curso = Route(id=1, depot_id=1, vehicle_id=1, date=HOY, status=RouteStatus.IN_PROGRESS)
        plan_day = self._caso(stops=[parada(1)], routes=[en_curso])

        with pytest.raises(PlanningError, match="en curso"):
            plan_day(depot_id=1, day=HOY, replan=True)

    def test_las_paradas_sin_asignar_vuelven_a_pendiente(self):
        resultado_planificador = PlanResult(
            routes=(planned(1, 1),), unassigned_stop_ids=(2,), metrics={}
        )
        plan_day = self._caso(stops=[parada(1), parada(2)], plan_result=resultado_planificador)

        resultado = plan_day(depot_id=1, day=HOY)

        assert [s.id for s in resultado.unassigned] == [2]
        assert self.stops.stops[2].status is StopStatus.PENDING

    def test_prefiere_al_chofer_habitual_del_vehiculo(self):
        habitual = Driver(
            id=7, username="chofer7", full_name="Chofer Siete", depot_id=1, default_vehicle_id=1
        )
        otro = Driver(id=8, username="chofer8", full_name="Chofer Ocho", depot_id=1)
        plan_day = self._caso(stops=[parada(1)], drivers=[otro, habitual])

        resultado = plan_day(depot_id=1, day=HOY)

        assert resultado.routes[0].driver_id == 7


class TestSincronizarLaColaDelChofer:
    def _caso(self, paradas=(1,), asignadas=(1,)):
        self.stops = FakeStopRepository([parada(i, StopStatus.PLANNED) for i in paradas])
        self.stops.assigned = {3: set(asignadas)}
        self.stops.planned_ids = set(paradas)
        self.events = FakeEventRepository()
        self.uow = FakeUnitOfWork()
        return SyncDriverEvents(events=self.events, stops=self.stops, uow=self.uow)

    def _evento(self, stop_id=1, kind=EventKind.DELIVERED, minutos=0, **extra):
        return DeliveryEvent(
            id=None,
            stop_id=stop_id,
            driver_id=3,
            client_event_id=extra.pop("client_event_id", uuid4()),
            kind=kind,
            occurred_at=AHORA - timedelta(minutes=minutos),
            **extra,
        )

    def test_guarda_los_hechos_y_proyecta_el_estado(self):
        sync = self._caso()

        reporte = sync(3, [self._evento()])

        assert reporte.created == 1
        assert self.stops.stops[1].status is StopStatus.DELIVERED

    def test_reenviar_la_misma_cola_no_duplica_nada(self):
        sync = self._caso()
        cola = [self._evento()]

        primera = sync(3, cola)
        segunda = sync(3, cola)

        assert primera.created == 1
        assert segunda.created == 0
        assert segunda.duplicates == 1
        assert len(self.events.events) == 1

    def test_una_tanda_parcialmente_repetida_solo_escribe_lo_nuevo(self):
        sync = self._caso(paradas=(1, 2), asignadas=(1, 2))
        viejo = self._evento(stop_id=1)
        sync(3, [viejo])

        reporte = sync(3, [viejo, self._evento(stop_id=2)])

        assert reporte.created == 1
        assert reporte.duplicates == 1

    def test_no_se_aceptan_hechos_sobre_paradas_ajenas(self):
        sync = self._caso(paradas=(1, 2), asignadas=(1,))

        with pytest.raises(StopNotAssignedToDriverError) as fallo:
            sync(3, [self._evento(stop_id=2)])

        assert fallo.value.stop_ids == [2]
        assert self.events.events == []

    def test_los_hechos_desordenados_se_resuelven_por_hora_del_dispositivo(self):
        sync = self._caso()

        sync(3, [self._evento(kind=EventKind.DELIVERED, minutos=0)])
        sync(3, [self._evento(kind=EventKind.DEPARTED, minutos=30)])

        assert self.stops.stops[1].status is StopStatus.DELIVERED

    def test_una_entrega_fallida_conserva_su_motivo(self):
        sync = self._caso()

        sync(3, [self._evento(kind=EventKind.FAILED, reason=FailureReason.ABSENT)])

        assert self.stops.stops[1].status is StopStatus.FAILED
        assert self.events.events[0].reason is FailureReason.ABSENT


class TestPosiciones:
    def test_los_reenvios_se_descartan_por_marca_de_tiempo(self):
        repo = FakePingRepository()
        sync = SyncDriverPings(repo)
        ping = LocationPing(driver_id=3, coordinates=Coordinates(23.1, -82.3), recorded_at=AHORA)

        assert sync([ping]) == 1
        assert sync([ping]) == 0


class TestRutaDelChofer:
    def test_sin_ruta_asignada_devuelve_nada_en_vez_de_lanzar(self):
        caso = GetDriverRoute(FakeRouteRepository(), FakeClock(AHORA))

        assert caso(driver_id=3) is None

    def test_usa_el_dia_de_hoy_cuando_no_se_pide_una_fecha(self):
        ruta = Route(id=1, depot_id=1, vehicle_id=1, date=HOY, driver_id=3)
        caso = GetDriverRoute(FakeRouteRepository([ruta]), FakeClock(AHORA))

        assert caso(driver_id=3).id == 1


class TestSeguimientoPublico:
    def test_devuelve_la_linea_de_tiempo_en_orden_y_sin_notas(self):
        stops = FakeStopRepository([parada(1)])
        events = FakeEventRepository()
        cronologia = [
            (EventKind.DELIVERED, 0),
            (EventKind.NOTE, 5),
            (EventKind.DEPARTED, 30),
        ]
        for kind, minutos in cronologia:
            events.append(
                DeliveryEvent(
                    id=None,
                    stop_id=1,
                    driver_id=3,
                    client_event_id=uuid4(),
                    kind=kind,
                    occurred_at=AHORA - timedelta(minutes=minutos),
                )
            )

        envio = TrackShipment(stops, events)("CODE0001")

        assert [e.kind for e in envio.timeline] == [EventKind.DEPARTED, EventKind.DELIVERED]

    def test_un_codigo_inexistente_es_un_error_de_negocio(self):
        with pytest.raises(StopNotFoundError):
            TrackShipment(FakeStopRepository(), FakeEventRepository())("NOEXISTE")
