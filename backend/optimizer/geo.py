"""Distancias geograficas y matriz de costos."""

from __future__ import annotations

import math
from collections.abc import Sequence

EARTH_RADIUS_KM = 6371.0088

# Factor de rodeo: la distancia por calle es mayor que la linea recta.
# 1.35 es el valor tipico reportado para malla urbana; se puede calibrar
# contra un servicio de ruteo real sin tocar el resto del solver.
DEFAULT_DETOUR_FACTOR = 1.35


class Point:
    """Coordenada geografica. Inmutable y hasheable."""

    __slots__ = ("lat", "lon")

    def __init__(self, lat: float, lon: float) -> None:
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"latitud fuera de rango: {lat}")
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"longitud fuera de rango: {lon}")
        object.__setattr__(self, "lat", float(lat))
        object.__setattr__(self, "lon", float(lon))

    def __setattr__(self, *_: object) -> None:
        raise AttributeError("Point es inmutable")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point) and (self.lat, self.lon) == (other.lat, other.lon)

    def __hash__(self) -> int:
        return hash((self.lat, self.lon))

    def __repr__(self) -> str:
        return f"Point({self.lat:.6f}, {self.lon:.6f})"


def haversine_km(a: Point, b: Point) -> float:
    """Distancia de circulo maximo entre dos puntos, en kilometros."""
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


class DistanceMatrix:
    """Matriz simetrica de distancias precalculada.

    El indice 0 es siempre el deposito; 1..n son las paradas en el orden dado.
    Se guarda solo el triangulo inferior en una lista plana: para 500 paradas
    son ~125k floats en vez de 250k, y el acceso sigue siendo O(1).
    """

    __slots__ = ("_data", "_n", "size")

    def __init__(
        self, points: Sequence[Point], detour_factor: float = DEFAULT_DETOUR_FACTOR
    ) -> None:
        if detour_factor < 1.0:
            raise ValueError("el factor de rodeo no puede ser menor que 1.0")
        n = len(points)
        self._n = n
        self.size = n
        data = [0.0] * (n * (n - 1) // 2)
        for i in range(1, n):
            base = i * (i - 1) // 2
            pi = points[i]
            for j in range(i):
                data[base + j] = haversine_km(pi, points[j]) * detour_factor
        self._data = data

    def __call__(self, i: int, j: int) -> float:
        if i == j:
            return 0.0
        if i < j:
            i, j = j, i
        return self._data[i * (i - 1) // 2 + j]

    def path_km(self, sequence: Sequence[int]) -> float:
        """Largo total de un recorrido dado como secuencia de indices."""
        return sum(self(sequence[k], sequence[k + 1]) for k in range(len(sequence) - 1))
