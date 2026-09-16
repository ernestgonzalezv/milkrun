"""Heuristica de ahorros de Clarke-Wright (version paralela).

Idea: arrancar con una ruta dedicada por parada (deposito -> i -> deposito) y
fusionar las que mas kilometros ahorran.

    ahorro(i, j) = d(deposito, i) + d(deposito, j) - d(i, j)

Un ahorro alto significa que i y j estan cerca entre si y lejos del deposito,
que es exactamente el par que conviene servir en el mismo viaje.
"""

from __future__ import annotations

from collections.abc import Sequence

from .geo import DistanceMatrix

DEPOT = 0


class RouteSet:
    """Conjunto de rutas en construccion, indexado por endpoints.

    Mantiene `owner` (parada -> id de ruta) para que preguntar "en que ruta
    esta esta parada" sea O(1) en vez de recorrer todas las rutas.
    """

    __slots__ = ("_next_id", "load", "owner", "routes")

    def __init__(self, stop_indices: Sequence[int], demands: dict[int, float]) -> None:
        self.routes: dict[int, list[int]] = {}
        self.load: dict[int, float] = {}
        self.owner: dict[int, int] = {}
        self._next_id = 0
        for s in stop_indices:
            rid = self._next_id
            self._next_id += 1
            self.routes[rid] = [s]
            self.load[rid] = demands[s]
            self.owner[s] = rid

    def is_endpoint(self, stop: int) -> bool:
        route = self.routes[self.owner[stop]]
        return stop in (route[0], route[-1])

    def merge(self, left_stop: int, right_stop: int) -> int:
        """Une la ruta de `left_stop` con la de `right_stop`.

        Orienta ambas para que la primera termine en `left_stop` y la segunda
        empiece en `right_stop`. Devuelve el id de la ruta resultante.
        """
        rid_a, rid_b = self.owner[left_stop], self.owner[right_stop]
        route_a, route_b = self.routes[rid_a], self.routes[rid_b]
        if route_a[0] == left_stop:
            route_a.reverse()
        if route_b[-1] == right_stop:
            route_b.reverse()
        merged = route_a + route_b
        self.routes[rid_a] = merged
        self.load[rid_a] += self.load[rid_b]
        for s in route_b:
            self.owner[s] = rid_a
        del self.routes[rid_b]
        del self.load[rid_b]
        return rid_a

    def as_lists(self) -> list[list[int]]:
        """Rutas ordenadas de forma determinista (por la parada mas chica)."""
        return sorted(self.routes.values(), key=lambda r: min(r))


def route_duration_minutes(
    matrix: DistanceMatrix,
    route: Sequence[int],
    service: dict[int, float],
    speed_kmh: float,
) -> float:
    """Duracion puerta a puerta de una ruta, deposito incluido en ambos extremos."""
    sequence = [DEPOT, *route, DEPOT]
    travel = matrix.path_km(sequence) / speed_kmh * 60.0
    return travel + sum(service[s] for s in route)


def clarke_wright(
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    capacity: float,
    max_shift_minutes: float,
    speed_kmh: float,
) -> list[list[int]]:
    """Construye rutas factibles maximizando el ahorro acumulado."""
    stops = sorted(demands)
    rs = RouteSet(stops, demands)

    savings = [
        (matrix(DEPOT, i) + matrix(DEPOT, j) - matrix(i, j), i, j)
        for idx, i in enumerate(stops)
        for j in stops[idx + 1 :]
    ]
    savings.sort(key=lambda t: (-t[0], t[1], t[2]))

    for saving, i, j in savings:
        if saving <= 0:
            break
        if rs.owner[i] == rs.owner[j]:
            continue
        if not (rs.is_endpoint(i) and rs.is_endpoint(j)):
            continue
        if rs.load[rs.owner[i]] + rs.load[rs.owner[j]] > capacity:
            continue

        route_a = list(rs.routes[rs.owner[i]])
        route_b = list(rs.routes[rs.owner[j]])
        if route_a[0] == i:
            route_a.reverse()
        if route_b[-1] == j:
            route_b.reverse()
        candidate = route_a + route_b
        if route_duration_minutes(matrix, candidate, service, speed_kmh) > max_shift_minutes:
            continue

        rs.merge(i, j)

    return rs.as_lists()


def consolidate(
    routes: list[list[int]],
    matrix: DistanceMatrix,
    demands: dict[int, float],
    service: dict[int, float],
    capacity: float,
    max_shift_minutes: float,
    speed_kmh: float,
    max_routes: int,
) -> list[list[int]]:
    """Reduce el numero de rutas cuando salieron mas que vehiculos disponibles.

    Clarke-Wright optimiza kilometros, no cantidad de rutas. Si quedan mas
    rutas que camiones, aqui se fusionan las que menos kilometros agregan
    aunque el ahorro sea negativo: es preferible manejar de mas a dejar
    paradas sin servir.
    """
    while len(routes) > max_routes:
        best: tuple[float, int, int, list[int]] | None = None
        for a in range(len(routes)):
            for b in range(len(routes)):
                if a == b:
                    continue
                ra, rb = routes[a], routes[b]
                if sum(demands[s] for s in ra) + sum(demands[s] for s in rb) > capacity:
                    continue
                for candidate in (ra + rb, ra + rb[::-1], ra[::-1] + rb, ra[::-1] + rb[::-1]):
                    duration = route_duration_minutes(matrix, candidate, service, speed_kmh)
                    if duration > max_shift_minutes:
                        continue
                    added = (
                        matrix.path_km([DEPOT, *candidate, DEPOT])
                        - matrix.path_km([DEPOT, *ra, DEPOT])
                        - matrix.path_km([DEPOT, *rb, DEPOT])
                    )
                    if best is None or added < best[0]:
                        best = (added, a, b, candidate)
        if best is None:
            break
        _, a, b, merged = best
        routes = [r for k, r in enumerate(routes) if k not in (a, b)]
        routes.append(merged)
    return sorted(routes, key=lambda r: min(r))
