"""Mathematical properties of the optimizer.

The suite in `test_solver.py` checks that the solver respects its constraints.
This one checks the arithmetic underneath them, and measures the one thing a
constraint test cannot: how far the heuristic lands from the true optimum.

For small instances the optimum is computable exactly, so it is computed here
rather than assumed. That turns "the plan looks reasonable" into a number.
"""

from __future__ import annotations

import math
from itertools import combinations, combinations_with_replacement, permutations

import pytest

from optimizer.geo import DEFAULT_DETOUR_FACTOR, DistanceMatrix, Point, haversine_km
from optimizer.models import Fleet, Stop, Vehicle
from optimizer.savings import DEPOT, route_duration_minutes
from optimizer.solver import solve

PARES_CONOCIDOS = [
    ("JFK", Point(40.6413, -73.7781), "LAX", Point(33.9416, -118.4085), 3974),
    ("JFK", Point(40.6413, -73.7781), "LHR", Point(51.4700, -0.4543), 5539),
    ("ORD", Point(41.9742, -87.9073), "LAX", Point(33.9416, -118.4085), 2802),
    ("HAV", Point(22.9892, -82.4091), "MIA", Point(25.7959, -80.2870), 379),
    ("SYD", Point(-33.9399, 151.1753), "AKL", Point(-37.0082, 174.7850), 2159),
]


@pytest.mark.parametrize(("a", "pa", "b", "pb", "km"), PARES_CONOCIDOS)
def test_haversine_reproduce_distancias_publicadas(a, pa, b, pb, km):
    calculada = haversine_km(pa, pb)

    assert calculada == pytest.approx(km, rel=0.005), f"{a}-{b}: {calculada:.0f} km vs {km} km"


def test_haversine_cruza_el_antimeridiano_por_el_lado_corto():
    """Dos puntos a un grado de distancia, uno a cada lado del meridiano 180."""
    oeste = Point(0.0, 179.5)
    este = Point(0.0, -179.5)

    assert haversine_km(oeste, este) == pytest.approx(111.3, rel=0.01)


def test_haversine_en_los_polos():
    polo_norte = Point(90.0, 0.0)
    polo_sur = Point(-90.0, 0.0)
    media_circunferencia = math.pi * 6371.0088

    assert haversine_km(polo_norte, polo_sur) == pytest.approx(media_circunferencia, rel=0.001)
    assert haversine_km(polo_norte, Point(90.0, 123.0)) == pytest.approx(0.0, abs=1e-9)


def _instancia(n: int, semilla: int, radio: float = 0.06):
    import random

    rng = random.Random(semilla)
    centro = Point(40.7220, -73.9090)
    paradas = tuple(
        Stop(
            id=f"S{i}",
            point=Point(
                centro.lat + rng.uniform(-radio, radio),
                centro.lon + rng.uniform(-radio, radio),
            ),
            demand=rng.randint(1, 3),
            service_minutes=5.0,
        )
        for i in range(n)
    )
    return centro, paradas


def test_el_ahorro_nunca_es_negativo_bajo_desigualdad_triangular():
    """s(i,j) = d(0,i) + d(0,j) - d(i,j).

    Con la desigualdad triangular d(i,j) <= d(0,i) + d(0,j), asi que el ahorro
    de unir dos paradas en un viaje no puede ser negativo. Si alguna vez lo
    fuera, la construccion estaria descartando uniones que si convienen.
    """
    centro, paradas = _instancia(14, semilla=3)
    m = DistanceMatrix([centro, *(p.point for p in paradas)], DEFAULT_DETOUR_FACTOR)

    for i, j in combinations(range(1, m.size), 2):
        ahorro = m(DEPOT, i) + m(DEPOT, j) - m(i, j)
        assert ahorro >= -1e-9, f"ahorro negativo entre {i} y {j}: {ahorro}"


def test_el_ahorro_esta_acotado_por_la_parada_mas_cercana():
    """s(i,j) <= 2 * min(d(0,i), d(0,j)).

    Se ahorra como mucho el ida y vuelta completo de la parada mas cercana al
    deposito. Un ahorro mayor solo puede venir de una matriz inconsistente.
    """
    centro, paradas = _instancia(14, semilla=4)
    m = DistanceMatrix([centro, *(p.point for p in paradas)], DEFAULT_DETOUR_FACTOR)

    for i, j in combinations(range(1, m.size), 2):
        ahorro = m(DEPOT, i) + m(DEPOT, j) - m(i, j)
        assert ahorro <= 2 * min(m(DEPOT, i), m(DEPOT, j)) + 1e-9


def _optimo_exacto(m: DistanceMatrix, demands, service, vehiculos) -> float:
    """Distancia minima real, enumerando todo el espacio de soluciones.

    Cualquier plan es una permutacion de las paradas partida en tramos, un
    tramo por vehiculo. Se enumeran las dos cosas. Solo es viable para
    instancias diminutas (el coste es n! por las particiones), que es
    exactamente el punto: por encima de eso hace falta la heuristica.
    """
    n = m.size - 1
    k = len(vehiculos)
    mejor = math.inf

    for orden in permutations(range(1, n + 1)):
        cortes_posibles = combinations_with_replacement(range(n + 1), k - 1) if k > 1 else [()]
        for cortes in cortes_posibles:
            limites = (0, *cortes, n)
            tramos = [orden[limites[t] : limites[t + 1]] for t in range(k)]

            total = 0.0
            posible = True
            for vehiculo, tramo in zip(vehiculos, tramos, strict=True):
                if not tramo:
                    continue
                if sum(demands[s] for s in tramo) > vehiculo.capacity + 1e-9:
                    posible = False
                    break
                duracion = route_duration_minutes(m, list(tramo), service, vehiculo.avg_speed_kmh)
                if duracion > vehiculo.max_shift_minutes + 1e-9:
                    posible = False
                    break
                total += m.path_km([DEPOT, *tramo, DEPOT])

            if posible and total < mejor:
                mejor = total

    return mejor


def _flota(centro, paradas, vehiculos: int, capacidad: float) -> Fleet:
    return Fleet(
        depot=centro,
        vehicles=tuple(
            Vehicle(f"V{i}", capacity=capacidad, max_shift_minutes=600.0) for i in range(vehiculos)
        ),
    )


def _brecha(plan, centro, paradas, flota) -> float:
    m = DistanceMatrix([centro, *(p.point for p in paradas)], DEFAULT_DETOUR_FACTOR)
    demands = {i + 1: p.demand for i, p in enumerate(paradas)}
    service = {i + 1: p.service_minutes for i, p in enumerate(paradas)}
    optimo = _optimo_exacto(m, demands, service, flota.vehicles)

    assert optimo < math.inf, "la instancia no tiene solucion factible; el test no mide nada"
    assert plan.total_distance_km >= optimo - 1e-6, (
        f"el plan ({plan.total_distance_km:.3f} km) esta por debajo del optimo "
        f"({optimo:.3f} km): el oraculo o el solver estan mal"
    )
    return (plan.total_distance_km - optimo) / optimo


@pytest.mark.parametrize("semilla", [1, 2, 3, 4, 5, 6])
def test_alcanza_el_optimo_exacto_cuando_la_capacidad_no_aprieta(semilla):
    """Con capacidad de sobra, el plan del solver ES el optimo. Exactamente.

    Seis paradas y dos vehiculos: 720 permutaciones por las particiones, un
    espacio recorrible entero. Clarke-Wright mas 2-opt y Or-opt no se queda
    cerca del optimo en esta escala, lo alcanza.

    Se verifico igualmente exacto hasta ocho paradas; n=8 tarda ~1.6 s por
    instancia en fuerza bruta y n=9 pasa de quince, asi que la suite se queda
    en seis. La asercion es igualdad y no una cota: una tolerancia del 20%
    cuando la realidad es 0% no detectaria una regresion del 15%.
    """
    centro, paradas = _instancia(6, semilla)
    flota = _flota(centro, paradas, vehiculos=2, capacidad=sum(p.demand for p in paradas))

    plan = solve(flota, paradas)

    assert plan.served_stops == len(paradas)
    assert _brecha(plan, centro, paradas, flota) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("semilla", [1, 2, 4, 5, 8])
def test_con_capacidad_ajustada_la_brecha_se_mantiene_bajo_control(semilla):
    """Donde la heuristica si cuesta: cuando la carga obliga a repartir.

    Con capacidad holgada el problema es solo en que orden visitar. En cuanto
    la capacidad obliga a usar varios vehiculos aparece la decision de QUE va
    con QUE, y ahi Clarke-Wright deja entre un 2% y un 12% sobre la mesa.

    El 15% es el techo observado mas un margen, no una aspiracion. Es la misma
    debilidad que el benchmark reporta contra OR-Tools con flota saturada.
    """
    centro, paradas = _instancia(7, semilla)
    flota = _flota(centro, paradas, vehiculos=3, capacidad=sum(p.demand for p in paradas) * 0.40)

    plan = solve(flota, paradas)

    if plan.served_stops < len(paradas):
        pytest.skip("la flota no cubre la demanda en esta instancia; lo mide otro test")

    assert _brecha(plan, centro, paradas, flota) <= 0.15


def test_duplicar_una_parada_en_el_mismo_punto_no_anade_recorrido():
    """Dos paquetes para la misma direccion son una parada, no dos viajes."""
    centro, paradas = _instancia(8, semilla=11)
    capacidad = sum(p.demand for p in paradas) * 3
    flota = Fleet(
        depot=centro, vehicles=(Vehicle("V0", capacity=capacidad, max_shift_minutes=900),)
    )

    base = solve(flota, paradas)
    gemela = Stop(id="GEMELA", point=paradas[0].point, demand=1.0, service_minutes=5.0)
    con_gemela = solve(flota, (*paradas, gemela))

    assert con_gemela.served_stops == base.served_stops + 1
    assert con_gemela.total_distance_km == pytest.approx(base.total_distance_km, abs=0.05)


def test_alejar_todas_las_paradas_del_deposito_alarga_el_plan():
    """Escalar las distancias tiene que escalar el recorrido, no reducirlo."""
    centro, paradas = _instancia(10, semilla=12, radio=0.03)
    lejanas = tuple(
        Stop(
            id=p.id,
            point=Point(
                centro.lat + (p.point.lat - centro.lat) * 2.0,
                centro.lon + (p.point.lon - centro.lon) * 2.0,
            ),
            demand=p.demand,
            service_minutes=p.service_minutes,
        )
        for p in paradas
    )
    capacidad = sum(p.demand for p in paradas) * 3
    flota = Fleet(
        depot=centro, vehicles=(Vehicle("V0", capacity=capacidad, max_shift_minutes=2000),)
    )

    cerca = solve(flota, paradas)
    lejos = solve(flota, lejanas)

    assert lejos.total_distance_km > cerca.total_distance_km
    assert lejos.total_distance_km <= cerca.total_distance_km * 2 * 1.01


def test_los_kilometros_reportados_coinciden_con_la_matriz():
    """Un plan que informa una distancia distinta de la que recorre es peor
    que uno malo: es uno en el que no se puede confiar para decidir nada."""
    centro, paradas = _instancia(24, semilla=21)
    capacidad = sum(p.demand for p in paradas) / 2
    flota = Fleet(
        depot=centro,
        vehicles=tuple(
            Vehicle(f"V{i}", capacity=capacidad, max_shift_minutes=600.0) for i in range(4)
        ),
    )

    plan = solve(flota, paradas)

    indices = {p.id: i + 1 for i, p in enumerate(paradas)}
    m = DistanceMatrix([centro, *(p.point for p in paradas)], DEFAULT_DETOUR_FACTOR)

    for ruta in plan.routes:
        recorrido = [DEPOT, *(indices[s] for s in ruta.stop_ids), DEPOT]
        assert ruta.distance_km == pytest.approx(m.path_km(recorrido), abs=1e-6)
        assert ruta.load == pytest.approx(
            sum(next(p.demand for p in paradas if p.id == s) for s in ruta.stop_ids), abs=1e-9
        )

    assert plan.total_distance_km == pytest.approx(
        sum(r.distance_km for r in plan.routes), abs=1e-9
    )
    assert plan.metrics["km_per_stop"] == pytest.approx(
        plan.total_distance_km / plan.served_stops, abs=1e-3
    )


def test_la_duracion_reportada_nunca_supera_la_jornada():
    centro, paradas = _instancia(30, semilla=22)
    flota = Fleet(
        depot=centro,
        vehicles=tuple(
            Vehicle(f"V{i}", capacity=25.0, max_shift_minutes=300.0, avg_speed_kmh=20.0)
            for i in range(5)
        ),
    )

    plan = solve(flota, paradas)

    for ruta in plan.routes:
        vehiculo = next(v for v in flota.vehicles if v.id == ruta.vehicle_id)
        assert ruta.duration_minutes <= vehiculo.max_shift_minutes + 1e-6
        assert ruta.duration_minutes > 0
