"""Referencia externa: OR-Tools como cota practica de calidad.

Los baselines de `baseline.py` miden contra lo que hace un despachador sin
software: mandar en el orden en que entraron los pedidos, o ir siempre al mas
cercano. Sirven para el argumento de negocio, pero no dicen que tan lejos del
optimo practico esta el solver, porque son rivales debiles.

Este modulo mide contra el estandar de la industria. OR-Tools es la libreria
de Google para este problema, y es lo que se usaria en un trabajo real. La
pregunta que responde no es "quien gana" sino "cuanto se pierde por haberlo
escrito a mano".

No es una comparacion de igual a igual y no pretende serlo:

    solver propio   ~0.5 s,  construccion + busqueda local
    OR-Tools        segundos, busqueda local guiada con metaheuristica

Se le da a OR-Tools un presupuesto de tiempo mayor A PROPOSITO. Ganarle
recortandole el tiempo no probaria nada; lo interesante es cuanta calidad
compra ese tiempo extra.

`ortools` es dependencia de desarrollo (requirements-dev.txt) y NO entra en la
imagen de produccion: son mas de 100 MB para algo que solo corre en el
benchmark. Por eso la importacion es perezosa y el fallo es explicito.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .baseline import BaselineResult
from .geo import DistanceMatrix
from .models import Vehicle
from .savings import DEPOT

METROS_POR_KM = 1000
SEGUNDOS_POR_MINUTO = 60

ESCALA_DEMANDA = 100

LIMITE_SEGUNDOS = 5.0

ESTRATEGIA_INICIAL = "PATH_CHEAPEST_ARC"


class OrToolsNoDisponibleError(RuntimeError):
    """Se pidio la referencia sin tener `ortools` instalado."""


def disponible() -> bool:
    """True si se puede calcular la referencia en este entorno."""
    try:
        import ortools.constraint_solver.pywrapcp  # noqa: F401
    except ImportError:
        return False
    return True


def ortools_reference(
    matrix: DistanceMatrix,
    demands: Mapping[int, float],
    service: Mapping[int, float],
    vehicles: Sequence[Vehicle],
    *,
    time_limit_seconds: float = LIMITE_SEGUNDOS,
    first_solution_strategy: str = ESTRATEGIA_INICIAL,
) -> BaselineResult:
    """Resuelve la misma instancia con OR-Tools, con las mismas restricciones.

    Recibe exactamente lo que reciben los baselines: la misma matriz de
    distancias, las mismas demandas, los mismos tiempos de servicio y la misma
    flota. Si alguna de esas cosas difiriera, la comparacion no mediria nada.
    """
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise OrToolsNoDisponibleError(
            "ortools no esta instalado. `pip install -r requirements-dev.txt`"
        ) from exc

    nodos = matrix.size
    if nodos <= 1 or not vehicles:
        return BaselineResult(routes=(), total_km=0.0, served=0)

    manager = pywrapcp.RoutingIndexManager(nodos, len(vehicles), DEPOT)
    routing = pywrapcp.RoutingModel(manager)

    def distancia_m(desde: int, hasta: int) -> int:
        i = manager.IndexToNode(desde)
        j = manager.IndexToNode(hasta)
        return round(matrix(i, j) * METROS_POR_KM)

    idx_distancia = routing.RegisterTransitCallback(distancia_m)
    routing.SetArcCostEvaluatorOfAllVehicles(idx_distancia)

    def demanda(desde: int) -> int:
        nodo = manager.IndexToNode(desde)
        return round(demands.get(nodo, 0.0) * ESCALA_DEMANDA)

    idx_demanda = routing.RegisterUnaryTransitCallback(demanda)
    routing.AddDimensionWithVehicleCapacity(
        idx_demanda,
        0,
        [round(v.capacity * ESCALA_DEMANDA) for v in vehicles],
        True,
        "Capacidad",
    )

    def hacer_tiempo(velocidad_kmh: float):
        def tiempo_s(desde: int, hasta: int) -> int:
            i = manager.IndexToNode(desde)
            j = manager.IndexToNode(hasta)
            viaje_min = matrix(i, j) / velocidad_kmh * 60.0
            servicio_min = service.get(i, 0.0) if i != DEPOT else 0.0
            return round((viaje_min + servicio_min) * SEGUNDOS_POR_MINUTO)

        return tiempo_s

    indices_tiempo = [
        routing.RegisterTransitCallback(hacer_tiempo(v.avg_speed_kmh)) for v in vehicles
    ]
    routing.AddDimensionWithVehicleTransitAndCapacity(
        indices_tiempo,
        0,
        [round(v.max_shift_minutes * SEGUNDOS_POR_MINUTO) for v in vehicles],
        True,
        "Jornada",
    )

    ida_y_vuelta_mas_cara = max(matrix(DEPOT, i) for i in range(1, nodos)) * 2
    penalizacion = round(ida_y_vuelta_mas_cara * METROS_POR_KM) * 10
    for nodo in range(1, nodos):
        routing.AddDisjunction([manager.NodeToIndex(nodo)], penalizacion)

    parametros = pywrapcp.DefaultRoutingSearchParameters()
    try:
        parametros.first_solution_strategy = getattr(
            routing_enums_pb2.FirstSolutionStrategy, first_solution_strategy
        )
    except AttributeError as exc:
        raise ValueError(f"estrategia inicial desconocida: {first_solution_strategy!r}") from exc
    parametros.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    parametros.time_limit.FromMilliseconds(int(time_limit_seconds * 1000))

    solucion = routing.SolveWithParameters(parametros)
    if solucion is None:
        return BaselineResult(routes=(), total_km=0.0, served=0)

    rutas: list[tuple[int, ...]] = []
    for vehiculo in range(len(vehicles)):
        indice = routing.Start(vehiculo)
        ruta: list[int] = []
        while not routing.IsEnd(indice):
            nodo = manager.IndexToNode(indice)
            if nodo != DEPOT:
                ruta.append(nodo)
            indice = solucion.Value(routing.NextVar(indice))
        if ruta:
            rutas.append(tuple(ruta))

    total_km = sum(matrix.path_km([DEPOT, *ruta, DEPOT]) for ruta in rutas)
    servidas = sum(len(ruta) for ruta in rutas)

    return BaselineResult(routes=tuple(rutas), total_km=total_km, served=servidas)
