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

#: OR-Tools trabaja con enteros. Las distancias van en metros y los tiempos en
#: segundos: con esa resolucion el error de redondeo es despreciable frente al
#: factor de rodeo de 1.35, que ya es una estimacion.
METROS_POR_KM = 1000
SEGUNDOS_POR_MINUTO = 60

#: La demanda es float (1.0, 2.5...). Se escala a centesimas para que la
#: dimension de capacidad pueda ser entera sin perder precision util.
ESCALA_DEMANDA = 100

#: Presupuesto por defecto. Con 400 paradas, mas tiempo sigue mejorando pero
#: con rendimientos decrecientes; 5 s deja la comparacion estable.
LIMITE_SEGUNDOS = 5.0

#: Estrategia de solucion inicial. Es un parametro y no una constante escondida
#: porque cambia el resultado: OR-Tools construye una primera solucion y luego
#: la mejora, asi que un arranque distinto puede terminar en otro optimo local.
#: SAVINGS es el mismo Clarke-Wright que usa el solver propio, y es la que hace
#: la comparacion justa; PATH_CHEAPEST_ARC es el defecto de la libreria.
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

    # --- Objetivo: kilometros ---------------------------------------------
    def distancia_m(desde: int, hasta: int) -> int:
        i = manager.IndexToNode(desde)
        j = manager.IndexToNode(hasta)
        return round(matrix(i, j) * METROS_POR_KM)

    idx_distancia = routing.RegisterTransitCallback(distancia_m)
    routing.SetArcCostEvaluatorOfAllVehicles(idx_distancia)

    # --- Restriccion de capacidad -----------------------------------------
    def demanda(desde: int) -> int:
        nodo = manager.IndexToNode(desde)
        return round(demands.get(nodo, 0.0) * ESCALA_DEMANDA)

    idx_demanda = routing.RegisterUnaryTransitCallback(demanda)
    routing.AddDimensionWithVehicleCapacity(
        idx_demanda,
        0,  # sin holgura: la carga no se puede "soltar" a mitad de ruta
        [round(v.capacity * ESCALA_DEMANDA) for v in vehicles],
        True,  # empezar la cuenta en cero al salir del deposito
        "Capacidad",
    )

    # --- Restriccion de jornada -------------------------------------------
    #
    # Un callback por vehiculo porque la velocidad puede variar entre ellos:
    # con flota mixta (motos y camionetas) el mismo tramo cuesta tiempos
    # distintos. El tiempo de servicio se cobra en el nodo de ORIGEN, que es
    # la convencion que hace que el acumulado al volver al deposito sea la
    # duracion total de la ruta.
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
        0,  # sin esperas permitidas
        [round(v.max_shift_minutes * SEGUNDOS_POR_MINUTO) for v in vehicles],
        True,
        "Jornada",
    )

    # --- Permitir dejar paradas sin servir --------------------------------
    #
    # Con flota saturada no cabe todo, y sin esto el modelo seria infactible y
    # OR-Tools devolveria None en vez de la mejor solucion parcial. La
    # penalizacion se fija por encima del coste de dedicarle un vehiculo entero
    # a una sola parada, para que dejarla fuera solo ocurra si de verdad no cabe.
    ida_y_vuelta_mas_cara = max(matrix(DEPOT, i) for i in range(1, nodos)) * 2
    penalizacion = round(ida_y_vuelta_mas_cara * METROS_POR_KM) * 10
    for nodo in range(1, nodos):
        routing.AddDisjunction([manager.NodeToIndex(nodo)], penalizacion)

    # --- Busqueda ----------------------------------------------------------
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

    # --- Lectura del resultado ---------------------------------------------
    #
    # Los kilometros se recalculan con `matrix.path_km`, el MISMO metodo que usa
    # el solver propio, y no con el objetivo interno de OR-Tools. Ese objetivo
    # esta en metros redondeados e incluye las penalizaciones por parada no
    # servida: compararlo contra kilometros reales seria comparar dos cosas
    # distintas.
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
