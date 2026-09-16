"""Referencias contra las que se mide el solver.

Sin una linea base no se puede afirmar que el optimizador sirve. Estas dos
son las que de verdad usa un despachador sin software: mandar en el orden en
que entraron los pedidos, o ir siempre al mas cercano.

Las dos corren con la MISMA flota y las MISMAS restricciones que el solver.
Compararse contra un baseline que puede usar camiones que no existen, o
saltarse la jornada maxima, no mide nada. Y como un baseline peor puede
terminar sirviendo menos paradas, cada uno reporta cuantas sirvio: la
comparacion justa es kilometros por parada entregada, no kilometros a secas.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .geo import DistanceMatrix
from .models import Vehicle
from .savings import DEPOT, route_duration_minutes


@dataclass(frozen=True, slots=True)
class BaselineResult:
    routes: tuple[tuple[int, ...], ...]
    total_km: float
    served: int

    @property
    def km_per_stop(self) -> float:
        return self.total_km / self.served if self.served else 0.0


def _fits(
    route: list[int],
    candidate: int,
    load: float,
    vehicle: Vehicle,
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
) -> bool:
    if load + demands[candidate] > vehicle.capacity:
        return False
    tentativa = [*route, candidate]
    duracion = route_duration_minutes(matrix, tentativa, service, vehicle.avg_speed_kmh)
    return duracion <= vehicle.max_shift_minutes


def _run(
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    vehicles: Sequence[Vehicle],
    *,
    nearest: bool,
) -> BaselineResult:
    pendientes = set(demands)
    rutas: list[tuple[int, ...]] = []
    total = 0.0

    for vehiculo in sorted(vehicles, key=lambda v: -v.capacity):
        ruta: list[int] = []
        carga = 0.0
        actual = DEPOT
        while pendientes:
            factibles = [
                s for s in pendientes if _fits(ruta, s, carga, vehiculo, matrix, demands, service)
            ]
            if not factibles:
                break
            siguiente = (
                min(factibles, key=lambda s: (matrix(actual, s), s)) if nearest else min(factibles)
            )
            ruta.append(siguiente)
            carga += demands[siguiente]
            pendientes.discard(siguiente)
            actual = siguiente
        if ruta:
            rutas.append(tuple(ruta))
            total += matrix.path_km([DEPOT, *ruta, DEPOT])

    return BaselineResult(routes=tuple(rutas), total_km=total, served=sum(len(r) for r in rutas))


def sequential(
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    vehicles: Sequence[Vehicle],
) -> BaselineResult:
    """Orden de llegada de los pedidos, cortado por capacidad y jornada."""
    return _run(matrix, demands, service, vehicles, nearest=False)


def nearest_neighbor(
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    vehicles: Sequence[Vehicle],
) -> BaselineResult:
    """Siempre a la parada mas cercana que todavia quepa en el vehiculo."""
    return _run(matrix, demands, service, vehicles, nearest=True)
