"""La referencia contra OR-Tools.

No se prueba que OR-Tools funcione (es de Google y ya esta probado), sino que
lo estamos usando BIEN: que reciba las mismas restricciones que el solver
propio y que lea el resultado con el mismo criterio. Un error aqui no se veria
como un fallo: se veria como una comparacion que parece razonable y no lo es.
"""

from __future__ import annotations

import pytest

from optimizer.geo import DEFAULT_DETOUR_FACTOR, DistanceMatrix, Point
from optimizer.models import Fleet, Stop, Vehicle
from optimizer.reference import disponible, ortools_reference
from optimizer.savings import DEPOT, route_duration_minutes
from optimizer.solver import solve

pytestmark = pytest.mark.skipif(
    not disponible(), reason="ortools es dependencia de desarrollo; no esta instalado"
)

HABANA = Point(23.1136, -82.3666)


def _instancia(n: int, semilla: int = 0) -> tuple[Stop, ...]:
    import random

    rng = random.Random(semilla)
    return tuple(
        Stop(
            id=f"S{i:03d}",
            point=Point(
                HABANA.lat + rng.uniform(-0.05, 0.05),
                HABANA.lon + rng.uniform(-0.07, 0.07),
            ),
            demand=rng.randint(1, 4),
            service_minutes=5.0,
        )
        for i in range(n)
    )


def _contexto(stops, vehiculos: int, cobertura: float = 1.5):
    capacidad = sum(s.demand for s in stops) * cobertura / vehiculos
    fleet = Fleet(
        depot=HABANA,
        vehicles=tuple(
            Vehicle(f"V{k}", capacity=capacidad, max_shift_minutes=600.0) for k in range(vehiculos)
        ),
    )
    matrix = DistanceMatrix([fleet.depot, *(s.point for s in stops)], DEFAULT_DETOUR_FACTOR)
    demands = {i + 1: s.demand for i, s in enumerate(stops)}
    service = {i + 1: s.service_minutes for i, s in enumerate(stops)}
    return fleet, matrix, demands, service


def test_sin_paradas_devuelve_resultado_vacio():
    fleet, _, _, _ = _contexto(_instancia(1), 1)
    vacia = DistanceMatrix([fleet.depot], DEFAULT_DETOUR_FACTOR)

    resultado = ortools_reference(vacia, {}, {}, fleet.vehicles, time_limit_seconds=1.0)

    assert resultado.served == 0
    assert resultado.total_km == 0.0


def test_sirve_todas_las_paradas_cuando_sobra_capacidad():
    stops = _instancia(20)
    fleet, matrix, demands, service = _contexto(stops, 3, cobertura=2.0)

    resultado = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=2.0)

    assert resultado.served == len(stops)


def test_ninguna_parada_aparece_dos_veces():
    """Un error de lectura de rutas duplicaria nodos y falsearia los km."""
    stops = _instancia(25)
    fleet, matrix, demands, service = _contexto(stops, 4)

    resultado = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=2.0)

    visitadas = [nodo for ruta in resultado.routes for nodo in ruta]
    assert len(visitadas) == len(set(visitadas))
    assert DEPOT not in visitadas


def test_respeta_la_capacidad_de_los_vehiculos():
    stops = _instancia(30)
    fleet, matrix, demands, service = _contexto(stops, 4, cobertura=1.1)

    resultado = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=3.0)

    capacidad = fleet.vehicles[0].capacity
    for ruta in resultado.routes:
        assert sum(demands[n] for n in ruta) <= capacidad + 0.01


def test_respeta_la_jornada_maxima():
    """La restriccion mas facil de escribir mal: el servicio se cobra en origen."""
    stops = _instancia(30)
    capacidad = sum(s.demand for s in stops)
    fleet = Fleet(
        depot=HABANA,
        vehicles=tuple(
            Vehicle(f"V{k}", capacity=capacidad, max_shift_minutes=120.0, avg_speed_kmh=25.0)
            for k in range(6)
        ),
    )
    matrix = DistanceMatrix([fleet.depot, *(s.point for s in stops)], DEFAULT_DETOUR_FACTOR)
    demands = {i + 1: s.demand for i, s in enumerate(stops)}
    service = {i + 1: s.service_minutes for i, s in enumerate(stops)}

    resultado = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=3.0)

    for ruta in resultado.routes:
        duracion = route_duration_minutes(matrix, list(ruta), service, 25.0)
        assert duracion <= 120.0 + 1.0


def test_deja_paradas_fuera_si_la_flota_no_alcanza():
    """Sin disyunciones el modelo seria infactible y devolveria None."""
    stops = _instancia(40)
    fleet, matrix, demands, service = _contexto(stops, 2, cobertura=0.5)

    resultado = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=3.0)

    assert 0 < resultado.served < len(stops)


def test_no_es_peor_que_el_solver_propio():
    """Si OR-Tools sale peor, es que lo estamos usando mal, no que seamos mejores.

    Con holgura del 5%: son heuristicas distintas y en una instancia concreta
    el orden puede invertirse. Una diferencia mayor sostenida indicaria que una
    restriccion esta mal traducida.
    """
    stops = _instancia(60, semilla=7)
    fleet, matrix, demands, service = _contexto(stops, 5, cobertura=1.5)

    plan = solve(fleet, stops)
    referencia = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=5.0)

    assert referencia.served >= plan.served_stops
    assert referencia.km_per_stop <= plan.metrics["km_per_stop"] * 1.05
