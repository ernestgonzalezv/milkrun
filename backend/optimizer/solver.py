"""Punto de entrada del optimizador: instancia de negocio -> plan de rutas.

Pipeline en cuatro fases. Cada una en su modulo y testeable por separado,
porque fallan distinto:

    1. construccion (savings.clarke_wright)  QUE paradas van juntas
    2. consolidacion (savings.consolidate)   ajusta al numero de vehiculos
    3. mejora local (local_search.refine)    EN QUE ORDEN visitarlas
    4. insercion                             mete lo que quedo suelto

Las fases 1-3 corren por rondas. Clarke-Wright asume flota homogenea y
trabaja con una sola capacidad; con flota mixta (motos y camionetas) eso
dejaria las unidades chicas ociosas, asi que la primera ronda planifica con
la capacidad mayor y las siguientes reintentan lo sobrante con los vehiculos
que quedaron libres.

La fase 4 existe porque las tres primeras optimizan kilometros, no cobertura.
Cuando la flota va ajustada eso deja paradas afuera aunque quede hueco en los
camiones: la insercion mas barata las mete donde menos desvio cuesten. En un
reparto real entregar una parada mas casi siempre vale mas que ahorrar 2 km.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from .baseline import BaselineResult, nearest_neighbor, sequential
from .geo import DEFAULT_DETOUR_FACTOR, DistanceMatrix
from .local_search import refine
from .models import Fleet, Plan, Route, Stop, Vehicle
from .savings import DEPOT, clarke_wright, consolidate, route_duration_minutes

#: Tope de rondas de construccion. Con flotas reales converge en 2 o 3; el
#: limite solo evita un bucle infinito si una ronda deja de hacer progreso.
MAX_ROUNDS = 4

#: Una asignacion es un vehiculo con su lista de paradas, por indice de matriz.
Assignment = tuple[Vehicle, list[int]]


def solve(
    fleet: Fleet,
    stops: Sequence[Stop],
    *,
    detour_factor: float = DEFAULT_DETOUR_FACTOR,
    improve: bool = True,
) -> Plan:
    """Arma el plan del dia para una flota y un conjunto de paradas."""
    started = time.perf_counter()

    if not stops:
        vacio = BaselineResult(routes=(), total_km=0.0, served=0)
        return Plan(routes=(), unassigned=(), metrics=_metrics(0.0, 0, vacio, vacio, started))

    ids = [s.id for s in stops]
    if len(set(ids)) != len(ids):
        raise ValueError("hay paradas con id repetido")

    matrix = DistanceMatrix([fleet.depot, *(s.point for s in stops)], detour_factor)
    index_to_stop = {i + 1: s for i, s in enumerate(stops)}
    demands = {i: s.demand for i, s in index_to_stop.items()}
    service = {i: s.service_minutes for i, s in index_to_stop.items()}

    assignments: list[Assignment] = []
    available = sorted(fleet.vehicles, key=lambda v: -v.capacity)
    pending = set(demands)

    for _ in range(MAX_ROUNDS):
        if not pending or not available:
            break
        nuevas = _plan_round(pending, available, matrix, demands, service, improve)
        if not nuevas:
            break  # ninguna ruta cupo en lo que queda de flota: no hay progreso
        assignments.extend(nuevas)
        pending -= {s for _, ruta in nuevas for s in ruta}

    _insert_pending(assignments, pending, matrix, demands, service, improve)

    served = sum(len(ruta) for _, ruta in assignments)
    seq = sequential(matrix, demands, service, fleet.vehicles)
    nn = nearest_neighbor(matrix, demands, service, fleet.vehicles)

    routes = tuple(
        Route(
            vehicle_id=vehiculo.id,
            stop_ids=tuple(index_to_stop[s].id for s in ruta),
            distance_km=matrix.path_km([DEPOT, *ruta, DEPOT]),
            load=sum(demands[s] for s in ruta),
            duration_minutes=route_duration_minutes(
                matrix, ruta, service, vehiculo.avg_speed_kmh
            ),
        )
        for vehiculo, ruta in sorted(assignments, key=lambda a: a[0].id)
        if ruta
    )
    return Plan(
        routes=routes,
        unassigned=tuple(index_to_stop[i].id for i in sorted(pending)),
        metrics=_metrics(
            sum(r.distance_km for r in routes), served, seq, nn, started
        ),
    )


def _plan_round(
    pending: set[int],
    available: list[Vehicle],
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    improve: bool,
) -> list[Assignment]:
    """Una ronda: construye rutas para lo pendiente y las asigna.

    Muta `available` quitando los vehiculos que quedan ocupados; devuelve las
    asignaciones creadas (vacio si ninguna ruta cupo).
    """
    capacity = max(v.capacity for v in available)
    shift = max(v.max_shift_minutes for v in available)
    # La velocidad mas baja de la flota disponible: se planifica con el caso
    # peor para no armar rutas que solo cierran si toca el vehiculo rapido.
    speed = min(v.avg_speed_kmh for v in available)

    sub_demands = {i: demands[i] for i in pending if demands[i] <= capacity}
    if not sub_demands:
        return []  # todo lo pendiente excede la capacidad del vehiculo mas grande
    sub_service = {i: service[i] for i in sub_demands}

    routes_idx = clarke_wright(
        matrix, sub_demands, sub_service,
        capacity=capacity, max_shift_minutes=shift, speed_kmh=speed,
    )
    if len(routes_idx) > len(available):
        routes_idx = consolidate(
            routes_idx, matrix, sub_demands, sub_service,
            capacity=capacity, max_shift_minutes=shift, speed_kmh=speed,
            max_routes=len(available),
        )
    if improve:
        routes_idx = [refine(r, matrix) for r in routes_idx]

    return _assign_to_vehicles(routes_idx, available, matrix, demands, service)


def _assign_to_vehicles(
    routes_idx: list[list[int]],
    available: list[Vehicle],
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
) -> list[Assignment]:
    """Empareja rutas con vehiculos: la ruta mas cargada al camion mas grande.

    Es greedy, no optimo, pero con flotas de decenas de vehiculos la
    diferencia es nula y se lee en unas pocas lineas. Las rutas que no caben
    en ningun vehiculo libre no se fuerzan: las intenta la ronda siguiente.
    """
    by_load = sorted(routes_idx, key=lambda r: (-sum(demands[s] for s in r), min(r) if r else 0))
    asignadas: list[Assignment] = []

    for route in by_load:
        load = sum(demands[s] for s in route)
        for k, vehicle in enumerate(available):
            if load > vehicle.capacity:
                continue
            duracion = route_duration_minutes(matrix, route, service, vehicle.avg_speed_kmh)
            if duracion > vehicle.max_shift_minutes:
                continue
            asignadas.append((vehicle, list(route)))
            available.pop(k)
            break

    return asignadas


def _insert_pending(
    assignments: list[Assignment],
    pending: set[int],
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    improve: bool,
) -> None:
    """Mete las paradas sueltas en la ruta y posicion mas baratas.

    Insercion mas barata clasica: para cada parada pendiente se prueba cada
    hueco de cada ruta y se elige el de menor desvio, siempre que la ruta
    siga cumpliendo capacidad y jornada. Se repite hasta que no entre ninguna.

    Se procesan las paradas grandes primero: cuando el hueco es escaso, la
    que mas cuesta acomodar es la que hay que colocar mientras todavia hay
    espacio, si no queda afuera por un pedido chico que entro antes.
    """
    if not assignments:
        return

    hubo_progreso = True
    while pending and hubo_progreso:
        hubo_progreso = False
        for parada in sorted(pending, key=lambda s: (-demands[s], s)):
            mejor: tuple[float, int, list[int]] | None = None
            for indice, (vehiculo, ruta) in enumerate(assignments):
                if sum(demands[s] for s in ruta) + demands[parada] > vehiculo.capacity:
                    continue
                actual_km = matrix.path_km([DEPOT, *ruta, DEPOT])
                for posicion in range(len(ruta) + 1):
                    candidata = [*ruta[:posicion], parada, *ruta[posicion:]]
                    duracion = route_duration_minutes(
                        matrix, candidata, service, vehiculo.avg_speed_kmh
                    )
                    if duracion > vehiculo.max_shift_minutes:
                        continue
                    desvio = matrix.path_km([DEPOT, *candidata, DEPOT]) - actual_km
                    if mejor is None or desvio < mejor[0]:
                        mejor = (desvio, indice, candidata)
            if mejor is None:
                continue
            _, indice, candidata = mejor
            assignments[indice] = (assignments[indice][0], candidata)
            pending.discard(parada)
            hubo_progreso = True

    if improve:
        for indice, (vehiculo, ruta) in enumerate(assignments):
            mejorada = refine(ruta, matrix)
            # Reordenar no cambia la carga, pero si la duracion: solo se acepta
            # si la ruta sigue cerrando dentro de la jornada del vehiculo.
            duracion = route_duration_minutes(matrix, mejorada, service, vehiculo.avg_speed_kmh)
            if duracion <= vehiculo.max_shift_minutes:
                assignments[indice] = (vehiculo, mejorada)


def _metrics(
    total_km: float,
    served: int,
    seq: BaselineResult,
    nn: BaselineResult,
    started: float,
) -> dict[str, float | int]:
    """Metricas del plan y de los baselines, listas para auditar.

    La mejora se calcula sobre kilometros por parada entregada. Usar
    kilometros a secas premiaria al metodo que entrega menos.
    """
    km_por_parada = total_km / served if served else 0.0

    def improvement(base: BaselineResult) -> float:
        if base.km_per_stop <= 0:
            return 0.0
        return round((base.km_per_stop - km_por_parada) / base.km_per_stop * 100, 2)

    return {
        "total_km": round(total_km, 3),
        "stops_served": served,
        "km_per_stop": round(km_por_parada, 3),
        "baseline_sequential_km": round(seq.total_km, 3),
        "baseline_sequential_stops": seq.served,
        "baseline_nearest_neighbor_km": round(nn.total_km, 3),
        "baseline_nearest_neighbor_stops": nn.served,
        "improvement_vs_sequential_pct": improvement(seq),
        "improvement_vs_nearest_neighbor_pct": improvement(nn),
        "solve_ms": round((time.perf_counter() - started) * 1000, 2),
    }
