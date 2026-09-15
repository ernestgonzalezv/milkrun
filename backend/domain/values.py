"""Objetos de valor: cosas que se identifican por su contenido, no por un id."""

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass
from enum import StrEnum

TRACKING_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin O/0 ni I/1/L
TRACKING_LENGTH = 8


class StopStatus(StrEnum):
    PENDING = "pending"
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {StopStatus.DELIVERED, StopStatus.FAILED, StopStatus.CANCELLED}


class EventKind(StrEnum):
    DEPARTED = "departed"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    FAILED = "failed"
    NOTE = "note"

    @property
    def projected_status(self) -> StopStatus | None:
        """Como este hecho afecta al estado de la parada.

        `None` significa que queda registrado pero no cambia el estado.
        """
        return {
            EventKind.DEPARTED: StopStatus.IN_TRANSIT,
            EventKind.ARRIVED: StopStatus.IN_TRANSIT,
            EventKind.DELIVERED: StopStatus.DELIVERED,
            EventKind.FAILED: StopStatus.FAILED,
        }.get(self)


class FailureReason(StrEnum):
    ABSENT = "absent"
    WRONG_ADDRESS = "wrong_address"
    REFUSED = "refused"
    NO_ACCESS = "no_access"
    OTHER = "other"


class RouteStatus(StrEnum):
    DRAFT = "draft"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    @property
    def is_replannable(self) -> bool:
        return self in {RouteStatus.DRAFT, RouteStatus.DISPATCHED}


@dataclass(frozen=True, slots=True)
class Coordinates:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitud fuera de rango: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitud fuera de rango: {self.longitude}")

    def distance_km(self, other: Coordinates) -> float:
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * 6371.0088 * math.asin(math.sqrt(h))


def new_tracking_code() -> str:
    """Codigo publico de seguimiento, pensado para dictarse por telefono."""
    return "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(TRACKING_LENGTH))
