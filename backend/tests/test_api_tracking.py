"""Seguimiento publico: el endpoint que ve cualquiera con el codigo.

Es la unica superficie sin autenticacion del sistema, asi que los tests se
enfocan en que no filtre nada de mas.
"""

from __future__ import annotations

import uuid

import pytest
from django.utils import timezone

from apps.deliveries.models import DeliveryEvent, EventKind, Stop, StopStatus
from config import container
from domain.entities import DeliveryEvent as DomainEvent
from domain.values import EventKind as DomainEventKind
from domain.values import FailureReason as DomainFailureReason

pytestmark = pytest.mark.django_db


@pytest.fixture
def parada(depot):
    return Stop.objects.create(
        depot=depot,
        customer_name="Yanet Perez Gomez",
        phone="+53 55512345",
        address="Calle 23 No. 456 e/ G y H, Vedado",
        latitude=23.1372,
        longitude=-82.3861,
        demand=2.0,
        notes="Interno del cliente, no publicar",
    )


def test_se_consulta_sin_token(api, parada):
    r = api.get(f"/api/v1/track/{parada.tracking_code}/")

    assert r.status_code == 200
    assert r.data["tracking_code"] == parada.tracking_code


def test_no_expone_telefono_ni_direccion_ni_notas(api, parada):
    """El codigo circula por WhatsApp: hay que asumir que llega a terceros."""
    r = api.get(f"/api/v1/track/{parada.tracking_code}/")

    cuerpo = str(r.data)
    assert "55512345" not in cuerpo
    assert "Calle 23" not in cuerpo
    assert "no publicar" not in cuerpo
    assert "latitude" not in r.data


def test_enmascara_los_apellidos_del_cliente(api, parada):
    r = api.get(f"/api/v1/track/{parada.tracking_code}/")

    assert r.data["customer_name"] == "Yanet P. G."


def test_la_linea_de_tiempo_llega_en_orden_cronologico(api, parada, drivers):
    chofer = drivers[0].user
    ahora = timezone.now()
    cronologia = [
        (30, EventKind.DEPARTED),
        (10, EventKind.ARRIVED),
        (0, EventKind.DELIVERED),
    ]
    for minutos, kind in cronologia:
        DeliveryEvent.objects.create(
            stop=parada,
            driver=chofer,
            client_event_id=uuid.uuid4(),
            kind=kind,
            occurred_at=ahora - timezone.timedelta(minutes=minutos),
        )

    r = api.get(f"/api/v1/track/{parada.tracking_code}/")

    tipos = [e["kind"] for e in r.data["timeline"]]
    assert tipos == ["departed", "arrived", "delivered"]


def test_un_codigo_inexistente_devuelve_404(api, db):
    assert api.get("/api/v1/track/NOEXISTE/").status_code == 404


def test_el_codigo_de_seguimiento_no_usa_caracteres_ambiguos(api, depot):
    """Se dicta por telefono: nada de O/0 ni I/1/L."""
    codigos = [
        Stop.objects.create(
            depot=depot,
            customer_name=f"C{i}",
            address="X",
            latitude=23.1,
            longitude=-82.3,
        ).tracking_code
        for i in range(30)
    ]

    assert all(len(c) == 8 for c in codigos)
    assert not set("".join(codigos)) & set("O0I1L")
    assert len(set(codigos)) == len(codigos), "no puede haber colisiones"


def test_el_estado_publico_sigue_la_proyeccion_de_la_bitacora(
    api, parada, drivers, ruta_con_parada
):
    """Se pasa por el caso de uso real, no se escribe el estado a mano.

    Si la proyeccion tuviera un bug, este test lo veria igual que produccion.
    """
    ruta_con_parada(parada)

    container.sync_driver_events()(
        drivers[0].user_id,
        [
            DomainEvent(
                id=None,
                stop_id=parada.id,
                driver_id=drivers[0].user_id,
                client_event_id=uuid.uuid4(),
                kind=DomainEventKind.FAILED,
                occurred_at=timezone.now(),
                reason=DomainFailureReason.ABSENT,
            )
        ],
    )

    r = api.get(f"/api/v1/track/{parada.tracking_code}/")

    assert r.data["status"] == StopStatus.FAILED
    assert r.data["status_display"] == "Failed"
    assert "absent" not in str(r.data)
