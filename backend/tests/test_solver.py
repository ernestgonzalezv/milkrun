"""Invariantes del solver completo.

Los tests estan escritos como propiedades sobre instancias generadas, no
como "para esta entrada esperada, esta salida esperada". Un plan de rutas
tiene demasiados grados de libertad para fijar la salida: lo que hay que
sostener es que ciertas cosas NUNCA pasan, sea cual sea la entrada.
"""

from __future__ import annotations

import pytest

from optimizer import Fleet, Point, Stop, Vehicle, solve
from optimizer.baseline import nearest_neighbor
from optimizer.geo import DEFAULT_DETOUR_FACTOR, DistanceMatrix, haversine_km

from .factories import HABANA, fleet_for_demand, homogeneous_fleet, random_stops

SEEDS = [1, 7, 13, 29, 64, 101]


@pytest.mark.parametrize("seed", SEEDS)
def test_toda_parada_aparece_exactamente_una_vez(seed):
    """Ni se pierde ni se duplica ninguna: la propiedad mas importante.

    Una parada perdida en un plan de reparto es un cliente que no recibe su
    pedido y nadie se entera hasta que llama.
    """
    fleet = homogeneous_fleet(5)
    stops = random_stops(80, seed=seed)

    plan = solve(fleet, stops)

    vistas = [sid for r in plan.routes for sid in r.stop_ids] + list(plan.unassigned)
    assert sorted(vistas) == sorted(s.id for s in stops)
    assert len(vistas) == len(set(vistas))


@pytest.mark.parametrize("seed", SEEDS)
def test_ningun_vehiculo_recibe_dos_rutas(seed):
    fleet = homogeneous_fleet(5)
    plan = solve(fleet, random_stops(60, seed=seed))

    usados = [r.vehicle_id for r in plan.routes]
    assert len(usados) == len(set(usados))
    assert len(usados) <= len(fleet.vehicles)


@pytest.mark.parametrize("seed", SEEDS)
def test_ninguna_ruta_excede_la_capacidad_de_su_vehiculo(seed):
    fleet = homogeneous_fleet(4, capacity=40.0)
    plan = solve(fleet, random_stops(70, seed=seed))

    capacidades = {v.id: v.capacity for v in fleet.vehicles}
    for ruta in plan.routes:
        assert ruta.load <= capacidades[ruta.vehicle_id] + 1e-9


@pytest.mark.parametrize("seed", SEEDS)
def test_ninguna_ruta_excede_la_jornada_maxima(seed):
    fleet = Fleet(
        depot=HABANA,
        vehicles=tuple(
            Vehicle(f"V{k}", capacity=100.0, max_shift_minutes=240.0, avg_speed_kmh=22.0)
            for k in range(6)
        ),
    )
    plan = solve(fleet, random_stops(50, seed=seed))

    for ruta in plan.routes:
        assert ruta.duration_minutes <= 240.0 + 1e-6


def test_la_carga_reportada_coincide_con_la_demanda_de_sus_paradas():
    fleet = homogeneous_fleet(4)
    stops = random_stops(50, seed=3)
    demanda = {s.id: s.demand for s in stops}

    plan = solve(fleet, stops)

    for ruta in plan.routes:
        assert ruta.load == pytest.approx(sum(demanda[sid] for sid in ruta.stop_ids))


@pytest.mark.parametrize("seed", SEEDS)
def test_el_plan_mejora_a_los_dos_baselines_con_flota_dimensionada(seed):
    """Caso normal de operacion: la flota alcanza para toda la demanda.

    Es el regimen en el que el optimizador tiene que ganar sin discusion, y
    donde el porcentaje del README es valido. Ver el test de flota saturada
    para el caso en que la ventaja se estrecha.
    """
    stops = random_stops(80, seed=seed)
    plan = solve(fleet_for_demand(stops), stops)

    assert plan.metrics["stops_served"] == 80
    assert plan.metrics["improvement_vs_sequential_pct"] > 60
    assert plan.metrics["improvement_vs_nearest_neighbor_pct"] > 8


@pytest.mark.parametrize("seed", SEEDS)
def test_con_flota_saturada_la_cobertura_se_mantiene_a_la_par_del_baseline(seed):
    """Limite conocido del solver, fijado como test para que no empeore.

    Clarke-Wright minimiza kilometros, no maximiza cobertura. Cuando la
    capacidad no alcanza para toda la demanda, el problema pasa a ser *que*
    paradas servir, y ahi la heuristica golosa compite de igual a igual. La
    fase de insercion mas barata cierra casi toda la brecha; lo que falta
    seria busqueda local entre rutas (relocate/swap), que hoy no esta.
    """
    stops = random_stops(80, seed=seed)
    plan = solve(homogeneous_fleet(5), stops)
    nn_sirve = plan.metrics["baseline_nearest_neighbor_stops"]

    assert plan.metrics["stops_served"] >= nn_sirve * 0.92


def test_la_mejora_local_reduce_o_iguala_la_distancia():
    fleet = homogeneous_fleet(5)
    stops = random_stops(80, seed=21)

    crudo = solve(fleet, stops, improve=False)
    pulido = solve(fleet, stops, improve=True)

    assert pulido.total_distance_km <= crudo.total_distance_km + 1e-9


def test_la_misma_entrada_produce_el_mismo_plan():
    """Reproducibilidad: sin esto, comparar dos versiones del solver es imposible."""
    fleet = homogeneous_fleet(4)
    stops = random_stops(60, seed=77)

    a, b = solve(fleet, stops), solve(fleet, stops)

    assert [(r.vehicle_id, r.stop_ids) for r in a.routes] == [
        (r.vehicle_id, r.stop_ids) for r in b.routes
    ]
    assert a.total_distance_km == b.total_distance_km


def test_el_orden_de_las_paradas_en_la_entrada_no_cambia_el_resultado():
    fleet = homogeneous_fleet(4)
    stops = random_stops(40, seed=5)

    directo = solve(fleet, stops)
    invertido = solve(fleet, tuple(reversed(stops)))

    assert directo.total_distance_km == pytest.approx(invertido.total_distance_km)


def test_el_solver_no_muta_su_entrada():
    fleet = homogeneous_fleet(3)
    stops = random_stops(30, seed=9)
    copia = tuple((s.id, s.point, s.demand) for s in stops)

    solve(fleet, stops)

    assert tuple((s.id, s.point, s.demand) for s in stops) == copia


def test_sin_paradas_devuelve_un_plan_vacio():
    plan = solve(homogeneous_fleet(2), ())

    assert plan.routes == ()
    assert plan.unassigned == ()
    assert plan.total_distance_km == 0.0


def test_una_sola_parada_genera_una_sola_ruta():
    stops = random_stops(1, seed=1)
    plan = solve(homogeneous_fleet(3), stops)

    assert len(plan.routes) == 1
    assert plan.routes[0].stop_ids == (stops[0].id,)


def test_una_parada_mas_pesada_que_todo_camion_queda_sin_asignar():
    """No se falla ni se reparte a la fuerza: se reporta para que la vea el humano."""
    fleet = homogeneous_fleet(2, capacity=10.0)
    stops = (
        Stop("normal", Point(23.12, -82.37), demand=5.0),
        Stop("gigante", Point(23.13, -82.38), demand=999.0),
    )

    plan = solve(fleet, stops)

    assert "gigante" in plan.unassigned
    assert "normal" not in plan.unassigned


def test_con_menos_vehiculos_que_carga_el_sobrante_se_reporta():
    fleet = homogeneous_fleet(1, capacity=20.0)
    stops = random_stops(40, seed=2, max_demand=5)

    plan = solve(fleet, stops)

    assert len(plan.routes) <= 1
    assert plan.unassigned, "con un solo camion chico tiene que sobrar carga"
    assert plan.served_stops + len(plan.unassigned) == len(stops)


def test_paradas_con_id_repetido_son_un_error():
    stops = (Stop("dup", Point(23.1, -82.3)), Stop("dup", Point(23.2, -82.4)))

    with pytest.raises(ValueError, match="id repetido"):
        solve(homogeneous_fleet(2), stops)


def test_una_flota_vacia_es_un_error():
    with pytest.raises(ValueError, match="vacia"):
        Fleet(depot=HABANA, vehicles=())


def test_capacidad_no_positiva_es_un_error():
    with pytest.raises(ValueError, match="capacidad"):
        Vehicle("V0", capacity=0)


def test_demanda_negativa_es_un_error():
    with pytest.raises(ValueError, match="demanda"):
        Stop("S1", Point(23.1, -82.3), demand=-1)


def test_la_flota_heterogenea_manda_la_ruta_mas_cargada_al_camion_mas_grande():
    fleet = Fleet(
        depot=HABANA,
        vehicles=(
            Vehicle("chico", capacity=15.0, max_shift_minutes=600.0),
            Vehicle("grande", capacity=60.0, max_shift_minutes=600.0),
        ),
    )
    plan = solve(fleet, random_stops(25, seed=6))

    por_vehiculo = {r.vehicle_id: r.load for r in plan.routes}
    if len(por_vehiculo) == 2:
        assert por_vehiculo["grande"] >= por_vehiculo["chico"]
    assert all(
        carga <= (15.0 if vid == "chico" else 60.0) + 1e-9 for vid, carga in por_vehiculo.items()
    )


@pytest.mark.parametrize("n", [10, 50, 150])
def test_escala_sin_explotar(n):
    """Cota de tiempo floja: detecta una regresion de complejidad, no mide rendimiento."""
    plan = solve(homogeneous_fleet(10, capacity=80.0), random_stops(n, seed=n))

    assert plan.metrics["solve_ms"] < 15_000
    assert plan.served_stops + len(plan.unassigned) == n


def test_los_baselines_corren_con_la_misma_flota_y_las_mismas_restricciones():
    """Un baseline que puede usar camiones inexistentes no mide nada.

    Se comprueba que las rutas del baseline respetan la capacidad real de la
    flota, y que reporta cuantas paradas alcanzo a servir para que la
    comparacion sea por kilometro entregado y no por kilometro a secas.
    """
    fleet = homogeneous_fleet(3, capacity=30.0)
    stops = random_stops(50, seed=31, max_demand=6)
    matriz = DistanceMatrix([HABANA, *(s.point for s in stops)], detour_factor=1.0)
    demandas = {i + 1: s.demand for i, s in enumerate(stops)}
    servicio = {i + 1: s.service_minutes for i, s in enumerate(stops)}

    nn = nearest_neighbor(matriz, demandas, servicio, fleet.vehicles)

    assert nn.routes, "el baseline tiene que producir alguna ruta"
    assert len(nn.routes) <= len(fleet.vehicles)
    for ruta in nn.routes:
        assert sum(demandas[i] for i in ruta) <= 30.0 + 1e-9
    assert nn.served == sum(len(r) for r in nn.routes)
    assert nn.km_per_stop == pytest.approx(nn.total_km / nn.served)

    plan = solve(fleet, stops)
    assert plan.metrics["baseline_nearest_neighbor_stops"] == nn.served


def test_lo_que_queda_sin_asignar_es_porque_de_verdad_no_cabe():
    """Verifica la postcondicion de la fase de insercion.

    Para cada parada que quedo afuera se prueba exhaustivamente cada hueco de
    cada ruta del plan. Si alguna combinacion resultara factible en capacidad
    y jornada, el solver dejo trabajo sin hacer y el test falla.
    """
    fleet = homogeneous_fleet(4, capacity=40.0)
    stops = random_stops(60, seed=44, max_demand=5)
    por_id = {s.id: s for s in stops}
    capacidad = {v.id: v.capacity for v in fleet.vehicles}
    jornada = {v.id: v.max_shift_minutes for v in fleet.vehicles}
    velocidad = {v.id: v.avg_speed_kmh for v in fleet.vehicles}

    plan = solve(fleet, stops)
    assert plan.unassigned, "la instancia tiene que saturar la flota"

    for sid in plan.unassigned:
        pendiente = por_id[sid]
        for ruta in plan.routes:
            if ruta.load + pendiente.demand > capacidad[ruta.vehicle_id] + 1e-9:
                continue
            actuales = [por_id[x] for x in ruta.stop_ids]
            for posicion in range(len(actuales) + 1):
                candidata = [*actuales[:posicion], pendiente, *actuales[posicion:]]
                duracion = _duracion(fleet.depot, candidata, velocidad[ruta.vehicle_id])
                assert duracion > jornada[ruta.vehicle_id], (
                    f"{sid} cabia en {ruta.vehicle_id} en la posicion {posicion}"
                )


def _duracion(depot, paradas, velocidad_kmh: float) -> float:
    """Duracion de una ruta candidata, replicando el calculo del solver."""
    secuencia = [depot, *(s.point for s in paradas), depot]
    km = sum(
        haversine_km(secuencia[k], secuencia[k + 1]) * DEFAULT_DETOUR_FACTOR
        for k in range(len(secuencia) - 1)
    )
    return km / velocidad_kmh * 60.0 + sum(s.service_minutes for s in paradas)


def test_la_flota_mixta_no_deja_las_unidades_chicas_ociosas():
    """Regresion: Clarke-Wright planificaba con la capacidad mayor y las motos
    quedaban sin usar mientras sobraban paradas sin asignar."""
    mixta = Fleet(
        depot=HABANA,
        vehicles=(
            Vehicle("moto-1", capacity=18.0, max_shift_minutes=420.0, avg_speed_kmh=28.0),
            Vehicle("moto-2", capacity=18.0, max_shift_minutes=420.0, avg_speed_kmh=28.0),
            Vehicle("camion-1", capacity=55.0, max_shift_minutes=480.0, avg_speed_kmh=22.0),
            Vehicle("camion-2", capacity=55.0, max_shift_minutes=480.0, avg_speed_kmh=22.0),
        ),
    )
    stops = random_stops(60, seed=2026, max_demand=5)

    plan = solve(mixta, stops)

    usados = {r.vehicle_id for r in plan.routes}
    assert {"moto-1", "moto-2"} & usados, "las motos tienen que entrar al plan"
    assert len(plan.routes) == 4
