"""Planificacion del dia: el endpoint que dispara el optimizador."""

from __future__ import annotations

import pytest

from apps.deliveries.models import StopStatus
from apps.routing.models import Route, RouteStatus

from .factories import HOY

pytestmark = pytest.mark.django_db


def _plan(client, depot, **extra):
    return client.post(
        "/api/v1/routes/plan/",
        {"depot": depot.id, "date": str(HOY), **extra},
        format="json",
    )


def test_planificar_crea_rutas_y_deja_las_paradas_en_planificada(
    as_dispatcher, depot, vehicles, drivers, stops_hoy
):
    r = _plan(as_dispatcher, depot)

    assert r.status_code == 201
    assert r.data["routes"], "tiene que crear al menos una ruta"
    assert Route.objects.filter(depot=depot, date=HOY).count() == len(r.data["routes"])

    for parada in stops_hoy:
        parada.refresh_from_db()
    servidas = [s for s in stops_hoy if s.status == StopStatus.PLANNED]
    assert len(servidas) == r.data["metrics"]["stops_served"]


def test_las_paradas_de_una_ruta_vienen_numeradas_desde_uno_y_sin_huecos(
    as_dispatcher, depot, vehicles, drivers, stops_hoy
):
    r = _plan(as_dispatcher, depot)

    for ruta in r.data["routes"]:
        secuencias = [p["sequence"] for p in ruta["stops"]]
        assert secuencias == list(range(1, len(secuencias) + 1))


def test_el_eta_crece_a_lo_largo_de_la_ruta(as_dispatcher, depot, vehicles, drivers, stops_hoy):
    r = _plan(as_dispatcher, depot)

    for ruta in r.data["routes"]:
        etas = [p["eta_minutes"] for p in ruta["stops"]]
        assert etas == sorted(etas)
        assert etas[0] > 0


def test_ninguna_parada_aparece_en_dos_rutas(as_dispatcher, depot, vehicles, drivers, stops_hoy):
    r = _plan(as_dispatcher, depot)

    vistas = [p["stop"]["id"] for ruta in r.data["routes"] for p in ruta["stops"]]
    assert len(vistas) == len(set(vistas))


def test_replanificar_sin_flag_devuelve_409(as_dispatcher, depot, vehicles, drivers, stops_hoy):
    _plan(as_dispatcher, depot)

    r = _plan(as_dispatcher, depot)

    assert r.status_code == 409
    assert "replan" in r.data["detail"]


def test_replanificar_con_flag_reemplaza_el_plan_anterior(
    as_dispatcher, depot, vehicles, drivers, stops_hoy
):
    primero = _plan(as_dispatcher, depot)
    ids_previos = {r["id"] for r in primero.data["routes"]}

    segundo = _plan(as_dispatcher, depot, replan=True)

    assert segundo.status_code == 201
    ids_nuevos = {r["id"] for r in segundo.data["routes"]}
    assert not (ids_previos & ids_nuevos), "las rutas viejas se borran, no se reciclan"
    assert Route.objects.filter(depot=depot, date=HOY).count() == len(ids_nuevos)


def test_no_se_replanifica_un_dia_que_ya_arranco(
    as_dispatcher, depot, vehicles, drivers, stops_hoy
):
    _plan(as_dispatcher, depot)
    Route.objects.filter(date=HOY).update(status=RouteStatus.IN_PROGRESS)

    r = _plan(as_dispatcher, depot, replan=True)

    assert r.status_code == 409
    assert "en curso" in r.data["detail"]


def test_un_deposito_sin_paradas_no_se_planifica(as_dispatcher, depot, vehicles, drivers):
    r = _plan(as_dispatcher, depot)

    assert r.status_code == 409
    assert "No hay paradas" in r.data["detail"]


def test_un_deposito_sin_vehiculos_activos_no_se_planifica(
    as_dispatcher, depot, vehicles, stops_hoy
):
    for v in vehicles:
        v.is_active = False
        v.save()

    r = _plan(as_dispatcher, depot)

    assert r.status_code == 409
    assert "vehiculos activos" in r.data["detail"]


def test_el_plan_no_queda_a_medias_si_algo_falla(
    as_dispatcher, depot, vehicles, drivers, stops_hoy, monkeypatch
):
    """La planificacion es atomica: un fallo a mitad no deja rutas huerfanas."""
    from infrastructure.planner import HaversineItinerary

    original = HaversineItinerary.legs
    llamadas = {"n": 0}

    def falla_en_la_segunda_ruta(self, *args, **kwargs):
        llamadas["n"] += 1
        if llamadas["n"] == 2:
            raise RuntimeError("fallo simulado")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(HaversineItinerary, "legs", falla_en_la_segunda_ruta)

    with pytest.raises(RuntimeError):
        _plan(as_dispatcher, depot)

    assert not Route.objects.filter(depot=depot, date=HOY).exists()
    for parada in stops_hoy:
        parada.refresh_from_db()
        assert parada.status == StopStatus.PENDING


def test_las_metricas_del_optimizador_quedan_guardadas_en_la_ruta(
    as_dispatcher, depot, vehicles, drivers, stops_hoy
):
    """Para poder auditar despues por que el plan salio como salio."""
    _plan(as_dispatcher, depot)

    ruta = Route.objects.filter(date=HOY).first()
    assert ruta.optimizer_metrics["stops_served"] > 0
    assert "improvement_vs_nearest_neighbor_pct" in ruta.optimizer_metrics
    assert ruta.optimizer_metrics["solve_ms"] >= 0


def test_el_detalle_de_una_ruta_no_dispara_un_n_mas_uno(
    as_dispatcher, depot, vehicles, drivers, stops_hoy, django_assert_max_num_queries
):
    """Cota de consultas: si alguien quita un prefetch, el test avisa."""
    r = _plan(as_dispatcher, depot)
    ruta_id = r.data["routes"][0]["id"]

    with django_assert_max_num_queries(6):
        as_dispatcher.get(f"/api/v1/routes/{ruta_id}/")


def test_el_listado_de_rutas_no_anida_las_paradas(
    as_dispatcher, depot, vehicles, drivers, stops_hoy, django_assert_max_num_queries
):
    _plan(as_dispatcher, depot)

    with django_assert_max_num_queries(4):
        r = as_dispatcher.get(f"/api/v1/routes/?date={HOY}")

    assert r.status_code == 200
    assert "stops" not in r.data["results"][0]
    assert r.data["results"][0]["stop_count"] > 0


def test_el_endpoint_de_planificacion_esta_limitado(
    as_dispatcher, depot, vehicles, drivers, stops_hoy, settings
):
    """Planificar es caro: se protege con un limite por minuto.

    Se baja el limite a 2 para no disparar veinte peticiones en un test.
    """
    from rest_framework.throttling import ScopedRateThrottle

    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["planning"] = "2/min"
    ScopedRateThrottle.THROTTLE_RATES = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    codigos = [_plan(as_dispatcher, depot, replan=True).status_code for _ in range(3)]

    assert codigos[:2] == [201, 201]
    assert codigos[2] == 429


def test_el_listado_expandido_trae_las_paradas_en_una_sola_peticion(
    as_dispatcher, depot, vehicles, drivers, stops_hoy, django_assert_max_num_queries
):
    """El mapa necesita el dia completo; sin `expand` seria una peticion por ruta."""
    _plan(as_dispatcher, depot)

    with django_assert_max_num_queries(6):
        r = as_dispatcher.get(f"/api/v1/routes/?date={HOY}&expand=stops")

    assert r.status_code == 200
    assert r.data["results"], "el dia planificado tiene rutas"
    for ruta in r.data["results"]:
        assert ruta["stops"], "cada ruta viene con sus paradas"
        assert "latitude" in ruta["stops"][0]["stop"]
