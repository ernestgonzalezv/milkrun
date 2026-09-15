"""Sincronizacion de la app movil: la parte que tiene que aguantar mala senal."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.deliveries.models import DeliveryEvent, LocationPing, StopStatus

from .factories import HOY

pytestmark = pytest.mark.django_db


@pytest.fixture
def ruta_del_chofer(as_dispatcher, api, depot, vehicles, drivers, stops_hoy):
    """Planifica el dia y devuelve (cliente autenticado como el chofer, ruta)."""
    r = as_dispatcher.post(
        "/api/v1/routes/plan/", {"depot": depot.id, "date": str(HOY)}, format="json"
    )
    assert r.status_code == 201
    ruta = r.data["routes"][0]

    from apps.accounts.models import User

    chofer = User.objects.get(id=ruta["driver"])
    api.force_authenticate(chofer)
    return api, ruta, chofer


def _evento(stop_id: int, kind: str = "delivered", **extra) -> dict:
    return {
        "stop": stop_id,
        "client_event_id": str(uuid.uuid4()),
        "kind": kind,
        "occurred_at": timezone.now().isoformat(),
        **extra,
    }


def test_el_chofer_recibe_su_ruta_del_dia(ruta_del_chofer):
    cliente, ruta, _ = ruta_del_chofer

    r = cliente.get(f"/api/v1/me/route/?date={HOY}")

    assert r.status_code == 200
    assert r.data["id"] == ruta["id"]
    assert len(r.data["stops"]) == len(ruta["stops"])


def test_sin_ruta_asignada_responde_204_y_no_404(as_driver):
    """204 y no 404: "hoy no te toca" no es un error, y la app lo distingue."""
    r = as_driver.get(f"/api/v1/me/route/?date={HOY}")

    assert r.status_code == 204


def test_un_chofer_no_ve_la_ruta_de_otro(ruta_del_chofer, api, drivers):
    _, ruta, chofer = ruta_del_chofer
    otro = next(d.user for d in drivers if d.user_id != chofer.id)
    api.force_authenticate(otro)

    r = api.get(f"/api/v1/me/route/?date={HOY}")

    assert r.status_code == 204 or r.data["id"] != ruta["id"]


def test_reenviar_la_misma_cola_no_duplica_eventos(ruta_del_chofer):
    cliente, ruta, _ = ruta_del_chofer
    cola = [_evento(ruta["stops"][0]["stop"]["id"]), _evento(ruta["stops"][1]["stop"]["id"])]

    primera = cliente.post("/api/v1/me/events/", {"events": cola}, format="json")
    segunda = cliente.post("/api/v1/me/events/", {"events": cola}, format="json")
    tercera = cliente.post("/api/v1/me/events/", {"events": cola}, format="json")

    assert primera.data["created"] == 2
    assert segunda.data["created"] == 0 and segunda.data["duplicates"] == 2
    assert tercera.data["created"] == 0
    assert all(r.status_code == 200 for r in (primera, segunda, tercera))
    assert DeliveryEvent.objects.count() == 2


def test_una_tanda_parcialmente_repetida_solo_escribe_lo_nuevo(ruta_del_chofer):
    """El caso real: la app reenvia la cola con un evento nuevo al final."""
    cliente, ruta, _ = ruta_del_chofer
    viejo = _evento(ruta["stops"][0]["stop"]["id"])
    cliente.post("/api/v1/me/events/", {"events": [viejo]}, format="json")

    nuevo = _evento(ruta["stops"][1]["stop"]["id"])
    r = cliente.post("/api/v1/me/events/", {"events": [viejo, nuevo]}, format="json")

    assert r.data["created"] == 1
    assert r.data["duplicates"] == 1
    assert DeliveryEvent.objects.count() == 2


def test_el_evento_proyecta_el_estado_de_la_parada(ruta_del_chofer):
    cliente, ruta, _ = ruta_del_chofer
    entregada = ruta["stops"][0]["stop"]
    fallida = ruta["stops"][1]["stop"]

    cliente.post(
        "/api/v1/me/events/",
        {
            "events": [
                _evento(entregada["id"], "delivered"),
                _evento(fallida["id"], "failed", reason="absent", note="Nadie abrio"),
            ]
        },
        format="json",
    )

    from apps.deliveries.models import Stop

    assert Stop.objects.get(id=entregada["id"]).status == StopStatus.DELIVERED
    assert Stop.objects.get(id=fallida["id"]).status == StopStatus.FAILED


def test_los_eventos_desordenados_se_resuelven_por_hora_del_dispositivo(ruta_del_chofer):
    """Caso tipico de cola offline: el evento viejo llega despues del nuevo.

    El chofer marca "en camino" en un sotano sin senal; para cuando el
    telefono recupera cobertura ya marco la entrega. Los dos salen juntos y
    el orden de llegada no dice nada: manda `occurred_at`.
    """
    cliente, ruta, _ = ruta_del_chofer
    parada = ruta["stops"][0]["stop"]
    ahora = timezone.now()

    tardio = _evento(parada["id"], "departed")
    tardio["occurred_at"] = (ahora - timedelta(minutes=30)).isoformat()
    reciente = _evento(parada["id"], "delivered")
    reciente["occurred_at"] = ahora.isoformat()

    # Se envian en el orden equivocado a proposito.
    cliente.post("/api/v1/me/events/", {"events": [reciente]}, format="json")
    cliente.post("/api/v1/me/events/", {"events": [tardio]}, format="json")

    from apps.deliveries.models import Stop

    assert Stop.objects.get(id=parada["id"]).status == StopStatus.DELIVERED


def test_no_se_aceptan_eventos_de_paradas_ajenas(ruta_del_chofer, stops_hoy):
    cliente, ruta, _ = ruta_del_chofer
    mias = {p["stop"]["id"] for p in ruta["stops"]}
    ajena = next(s for s in stops_hoy if s.id not in mias)

    r = cliente.post("/api/v1/me/events/", {"events": [_evento(ajena.id)]}, format="json")

    assert r.status_code == 403
    assert DeliveryEvent.objects.count() == 0


def test_una_entrega_fallida_sin_motivo_se_rechaza(ruta_del_chofer):
    cliente, ruta, _ = ruta_del_chofer

    r = cliente.post(
        "/api/v1/me/events/",
        {"events": [_evento(ruta["stops"][0]["stop"]["id"], "failed")]},
        format="json",
    )

    assert r.status_code == 400
    assert "motivo" in str(r.data).lower()


def test_una_tanda_vacia_se_rechaza(ruta_del_chofer):
    cliente, _, _ = ruta_del_chofer

    assert cliente.post("/api/v1/me/events/", {"events": []}, format="json").status_code == 400


def test_la_bitacora_conserva_todos_los_eventos_de_una_parada(ruta_del_chofer):
    """Append-only: el segundo evento no pisa al primero."""
    cliente, ruta, _ = ruta_del_chofer
    parada = ruta["stops"][0]["stop"]

    cliente.post(
        "/api/v1/me/events/",
        {"events": [_evento(parada["id"], "arrived"), _evento(parada["id"], "delivered")]},
        format="json",
    )

    assert DeliveryEvent.objects.filter(stop_id=parada["id"]).count() == 2


def test_las_posiciones_gps_se_guardan_y_los_reenvios_se_descartan(ruta_del_chofer):
    cliente, _, _ = ruta_del_chofer
    ahora = timezone.now()
    pings = [
        {
            "latitude": 23.11 + i * 0.001,
            "longitude": -82.36,
            "accuracy_m": 12.0,
            "speed_kmh": 24.0,
            "recorded_at": (ahora + timedelta(seconds=15 * i)).isoformat(),
        }
        for i in range(5)
    ]

    primera = cliente.post("/api/v1/me/pings/", {"pings": pings}, format="json")
    segunda = cliente.post("/api/v1/me/pings/", {"pings": pings}, format="json")

    assert primera.status_code == 202 and primera.data["created"] == 5
    assert segunda.data["created"] == 0
    assert LocationPing.objects.count() == 5
