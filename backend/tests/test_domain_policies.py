"""Reglas puras del dominio. Sin base de datos, sin Django, sin HTTP."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from domain.entities import DeliveryEvent, Stop
from domain.policies import project_status
from domain.values import Coordinates, EventKind, FailureReason, StopStatus

AHORA = datetime(2026, 9, 12, 14, 0)


def parada(status: StopStatus = StopStatus.PENDING) -> Stop:
    return Stop(
        id=1,
        tracking_code="ZU6P6E6K",
        depot_id=1,
        customer_name="Yanet Perez Gomez",
        address="Calle 23 No. 456, Vedado",
        coordinates=Coordinates(23.1372, -82.3861),
        scheduled_date=date(2026, 9, 12),
        status=status,
    )


def evento(kind: EventKind, minutos: int = 0, **extra) -> DeliveryEvent:
    return DeliveryEvent(
        id=None,
        stop_id=1,
        driver_id=3,
        client_event_id=uuid4(),
        kind=kind,
        occurred_at=AHORA - timedelta(minutes=minutos),
        **extra,
    )


class TestProyeccionDeEstado:
    def test_sin_eventos_una_parada_planificada_queda_planificada(self):
        assert project_status(parada(), [], is_planned=True) is StopStatus.PLANNED

    def test_sin_eventos_ni_ruta_queda_pendiente(self):
        assert project_status(parada(), [], is_planned=False) is StopStatus.PENDING

    def test_el_ultimo_hecho_manda(self):
        eventos = [evento(EventKind.DEPARTED, 30), evento(EventKind.DELIVERED, 0)]

        assert project_status(parada(), eventos, is_planned=True) is StopStatus.DELIVERED

    def test_el_orden_de_llegada_no_importa_solo_la_hora_del_dispositivo(self):
        """El caso real de la cola offline: el hecho viejo llega despues.

        El chofer marca "sali hacia la parada" en un sotano sin senal; para
        cuando el telefono recupera cobertura ya marco la entrega. Los dos
        salen juntos y el orden de llegada no dice nada.
        """
        desordenados = [evento(EventKind.DELIVERED, 0), evento(EventKind.DEPARTED, 30)]

        assert project_status(parada(), desordenados, is_planned=True) is StopStatus.DELIVERED

    def test_una_nota_no_cambia_el_estado(self):
        eventos = [evento(EventKind.DELIVERED, 10), evento(EventKind.NOTE, 0)]

        assert project_status(parada(), eventos, is_planned=True) is StopStatus.DELIVERED

    def test_cancelar_es_decision_de_oficina_y_el_terreno_no_la_revierte(self):
        eventos = [evento(EventKind.DELIVERED, 0)]

        proyectado = project_status(parada(StopStatus.CANCELLED), eventos, is_planned=True)

        assert proyectado is StopStatus.CANCELLED

    def test_llegar_deja_la_parada_en_camino(self):
        assert project_status(parada(), [evento(EventKind.ARRIVED)], is_planned=True) is (
            StopStatus.IN_TRANSIT
        )


class TestInvariantesDeEntidad:
    def test_una_entrega_fallida_sin_motivo_no_se_puede_construir(self):
        with pytest.raises(ValueError, match="motivo"):
            evento(EventKind.FAILED)

    def test_una_entrega_fallida_con_motivo_si(self):
        assert evento(EventKind.FAILED, reason=FailureReason.ABSENT).kind is EventKind.FAILED

    def test_el_nombre_publico_va_con_apellidos_enmascarados(self):
        assert parada().masked_customer_name() == "Yanet P. G."

    def test_una_coordenada_fuera_de_rango_es_un_error(self):
        with pytest.raises(ValueError, match="latitud"):
            Coordinates(91.0, 0.0)

    def test_los_estados_terminales_cierran_la_parada(self):
        assert StopStatus.DELIVERED.is_terminal
        assert StopStatus.FAILED.is_terminal
        assert not StopStatus.PLANNED.is_terminal
        assert not parada(StopStatus.DELIVERED).is_open
