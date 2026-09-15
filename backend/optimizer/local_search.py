"""Mejora local de rutas ya construidas: 2-opt y Or-opt.

Clarke-Wright decide *que* paradas van juntas; la busqueda local decide en
*que orden* visitarlas. Las dos fases son independientes, y por eso el
modulo no sabe nada de capacidades: reordenar no cambia la carga.

Invariante que sostienen las dos funciones: nunca devuelven una ruta mas
larga que la que recibieron, y nunca cambian el conjunto de paradas.
"""

from __future__ import annotations

from collections.abc import Sequence

from .geo import DistanceMatrix

DEPOT = 0
MAX_PASSES = 100
EPSILON = 1e-9


def two_opt(route: Sequence[int], matrix: DistanceMatrix) -> list[int]:
    """Elimina cruces invirtiendo tramos.

    Para el tramo a -> b ... c -> d, invertirlo da a -> c ... b -> d. Como la
    matriz es simetrica el interior del tramo cuesta lo mismo, asi que el
    delta se calcula con cuatro aristas y no recorriendo la ruta entera:

        delta = d(a,c) + d(b,d) - d(a,b) - d(c,d)
    """
    best = [DEPOT, *route, DEPOT]
    n = len(best)
    if n <= 4:  # deposito + 2 paradas: no hay nada que invertir
        return list(route)

    for _ in range(MAX_PASSES):
        improved = False
        for i in range(1, n - 2):
            a, b = best[i - 1], best[i]
            for j in range(i + 1, n - 1):
                c, d = best[j], best[j + 1]
                delta = matrix(a, c) + matrix(b, d) - matrix(a, b) - matrix(c, d)
                if delta < -EPSILON:
                    best[i : j + 1] = reversed(best[i : j + 1])
                    improved = True
                    a, b = best[i - 1], best[i]
        if not improved:
            break
    return best[1:-1]


def or_opt(route: Sequence[int], matrix: DistanceMatrix, max_segment: int = 3) -> list[int]:
    """Reubica tramos cortos (1 a 3 paradas) en otro punto de la ruta.

    Cubre el caso que 2-opt no ve: una parada bien ubicada geometricamente
    pero insertada en el bloque equivocado del recorrido.
    """
    best = [DEPOT, *route, DEPOT]
    if len(best) <= 4:
        return list(route)

    for _ in range(MAX_PASSES):
        improved = False
        for seg_len in range(1, max_segment + 1):
            for start in range(1, len(best) - seg_len):
                end = start + seg_len
                segment = best[start:end]
                remainder = best[:start] + best[end:]
                removed = (
                    matrix(best[start - 1], segment[0])
                    + matrix(segment[-1], best[end])
                    - matrix(best[start - 1], best[end])
                )
                for pos in range(1, len(remainder)):
                    if pos == start:
                        continue  # volveria a dejarlo donde estaba
                    prev, nxt = remainder[pos - 1], remainder[pos]
                    for piece in (segment, segment[::-1]):
                        added = (
                            matrix(prev, piece[0])
                            + matrix(piece[-1], nxt)
                            - matrix(prev, nxt)
                        )
                        if added - removed < -EPSILON:
                            best = remainder[:pos] + list(piece) + remainder[pos:]
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
        if not improved:
            break
    return best[1:-1]


def refine(route: Sequence[int], matrix: DistanceMatrix) -> list[int]:
    """Alterna 2-opt y Or-opt hasta que ninguno de los dos mejore."""
    current = list(route)
    current_km = matrix.path_km([DEPOT, *current, DEPOT])
    for _ in range(MAX_PASSES):
        candidate = or_opt(two_opt(current, matrix), matrix)
        candidate_km = matrix.path_km([DEPOT, *candidate, DEPOT])
        if candidate_km >= current_km - EPSILON:
            break
        current, current_km = candidate, candidate_km
    return current
