"""Desglose tramo a tramo de una ruta ya ordenada.

El solver devuelve totales; para pintar el mapa y darle un ETA al cliente
hace falta el detalle por parada. Se calcula aparte porque no interviene en
la optimizacion: es presentacion del resultado, no parte del algoritmo.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .geo import DEFAULT_DETOUR_FACTOR, Point, haversine_km


@dataclass(frozen=True, slots=True)
class Leg:
    """Tramo desde la parada anterior (o el deposito) hasta esta parada."""

    distance_km: float
    eta_minutes: float


def legs(
    depot: Point,
    points: Sequence[Point],
    service_minutes: Sequence[float],
    speed_kmh: float,
    detour_factor: float = DEFAULT_DETOUR_FACTOR,
) -> list[Leg]:
    """Distancia y ETA acumulado de cada parada, en el orden dado.

    El ETA incluye el tiempo de servicio de las paradas anteriores pero no el
    de la propia: es la hora estimada de *llegada*, no la de salida.
    """
    if len(points) != len(service_minutes):
        raise ValueError("puntos y tiempos de servicio deben tener el mismo largo")

    resultado: list[Leg] = []
    anterior = depot
    acumulado = 0.0
    for indice, punto in enumerate(points):
        distancia = haversine_km(anterior, punto) * detour_factor
        acumulado += distancia / speed_kmh * 60.0
        resultado.append(Leg(distance_km=round(distancia, 3), eta_minutes=round(acumulado, 1)))
        acumulado += service_minutes[indice]
        anterior = punto
    return resultado
