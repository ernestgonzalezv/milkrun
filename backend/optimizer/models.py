"""Tipos de dominio del optimizador.

Todo es inmutable a proposito: el solver nunca muta su entrada, asi que la
misma instancia se puede resolver varias veces con parametros distintos y
comparar resultados sin sorpresas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .geo import Point

__all__ = ["Fleet", "Plan", "Point", "Route", "Stop", "Vehicle"]


@dataclass(frozen=True, slots=True)
class Stop:
    """Una parada de entrega."""

    id: str
    point: Point
    demand: float = 1.0
    service_minutes: float = 5.0

    def __post_init__(self) -> None:
        if self.demand < 0:
            raise ValueError(f"parada {self.id}: la demanda no puede ser negativa")
        if self.service_minutes < 0:
            raise ValueError(f"parada {self.id}: el tiempo de servicio no puede ser negativo")


@dataclass(frozen=True, slots=True)
class Vehicle:
    """Un vehiculo disponible para el dia."""

    id: str
    capacity: float
    max_shift_minutes: float = 8 * 60
    avg_speed_kmh: float = 25.0

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"vehiculo {self.id}: la capacidad debe ser positiva")
        if self.avg_speed_kmh <= 0:
            raise ValueError(f"vehiculo {self.id}: la velocidad debe ser positiva")


@dataclass(frozen=True, slots=True)
class Fleet:
    """Flota homogenea o heterogenea que sale de un unico deposito."""

    depot: Point
    vehicles: tuple[Vehicle, ...]

    def __post_init__(self) -> None:
        if not self.vehicles:
            raise ValueError("la flota no puede estar vacia")
        ids = [v.id for v in self.vehicles]
        if len(set(ids)) != len(ids):
            raise ValueError("hay identificadores de vehiculo repetidos")

    @property
    def max_capacity(self) -> float:
        return max(v.capacity for v in self.vehicles)

    @property
    def total_capacity(self) -> float:
        return sum(v.capacity for v in self.vehicles)


@dataclass(frozen=True, slots=True)
class Route:
    """Recorrido asignado a un vehiculo: deposito -> paradas -> deposito."""

    vehicle_id: str
    stop_ids: tuple[str, ...]
    distance_km: float
    load: float
    duration_minutes: float

    @property
    def is_empty(self) -> bool:
        return not self.stop_ids


@dataclass(frozen=True, slots=True)
class Plan:
    """Resultado del solver."""

    routes: tuple[Route, ...]
    unassigned: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def total_distance_km(self) -> float:
        return sum(r.distance_km for r in self.routes)

    @property
    def used_vehicles(self) -> int:
        return sum(1 for r in self.routes if not r.is_empty)

    @property
    def served_stops(self) -> int:
        return sum(len(r.stop_ids) for r in self.routes)
