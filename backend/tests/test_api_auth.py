"""Autenticacion y permisos por rol."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_se_obtiene_un_par_de_tokens_con_credenciales_validas(api, dispatcher):
    r = api.post(
        "/api/v1/auth/token/",
        {"username": "marta", "password": "clave-de-prueba"},
        format="json",
    )

    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data


def test_credenciales_invalidas_no_devuelven_token(api, dispatcher):
    r = api.post(
        "/api/v1/auth/token/", {"username": "marta", "password": "incorrecta"}, format="json"
    )

    assert r.status_code == 401
    assert "access" not in r.data


def test_sin_token_la_api_responde_401(api):
    assert api.get("/api/v1/stops/").status_code == 401
    assert api.get("/api/v1/routes/").status_code == 401


def test_me_devuelve_el_rol_del_usuario(as_driver, drivers):
    r = as_driver.get("/api/v1/auth/me/")

    assert r.status_code == 200
    assert r.data["role"] == "driver"
    assert r.data["username"] == "chofer1"


def test_un_chofer_no_puede_crear_paradas(as_driver, depot):
    r = as_driver.post(
        "/api/v1/stops/",
        {
            "depot": depot.id,
            "customer_name": "X",
            "address": "Y",
            "latitude": 23.1,
            "longitude": -82.3,
        },
        format="json",
    )

    assert r.status_code == 403
    assert "despachador" in r.data["detail"].lower()


def test_un_chofer_puede_leer_paradas(as_driver, stops_hoy):
    assert as_driver.get("/api/v1/stops/").status_code == 200


def test_un_chofer_no_puede_cambiar_la_capacidad_de_un_vehiculo(as_driver, vehicles):
    r = as_driver.patch(f"/api/v1/vehicles/{vehicles[0].id}/", {"capacity": 9999}, format="json")

    assert r.status_code == 403
    vehicles[0].refresh_from_db()
    assert vehicles[0].capacity == 60.0


def test_un_despachador_no_puede_usar_los_endpoints_del_chofer(as_dispatcher):
    assert as_dispatcher.get("/api/v1/me/route/").status_code == 403
    r = as_dispatcher.post("/api/v1/me/events/", {"events": []}, format="json")
    assert r.status_code == 403
