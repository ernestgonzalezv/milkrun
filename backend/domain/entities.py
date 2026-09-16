"""Entidades del negocio.

Son dataclasses inmutables, no modelos de Django: el dominio no sabe que los
datos se guardan en una base relacional, y por eso puede testearse sin una.
El `id` es `None` mientras la entidad no se haya persistido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

from .values import Coordinates, EventKind, FailureReason, RouteStatus, StopStatus


@dataclass(frozen=True, slots=True)
class Depot:
    id: int | None
    name: str
    address: str
    coordinates: Coordinates
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class Vehicle:
    id: int | None
    depot_id: int
    code: str
    capacity: float
    max_shift_minutes: int = 480
    avg_speed_kmh: float = 25.0
    plate: str = ""
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"vehiculo {self.code}: la capacidad debe ser positiva")


@dataclass(frozen=True, slots=True)
class Driver:
    id: int
    username: str
    full_name: str
    depot_id: int | None = None
    default_vehicle_id: int | None = None
    is_available: bool = True


@dataclass(frozen=True, slots=True)
class Stop:
    id: int | None
    tracking_code: str
    depot_id: int
    customer_name: str
    address: str
    coordinates: Coordinates
    scheduled_date: date
    demand: float = 1.0
    service_minutes: int = 5
    status: StopStatus = StopStatus.PENDING
    phone: str = ""
    notes: str = ""
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.demand < 0:
            raise ValueError("la demanda no puede ser negativa")

    @property
    def is_open(self) -> bool:
        return not self.status.is_terminal

    def masked_customer_name(self) -> str:
        """Nombre para el seguimiento publico.

        El codigo de seguimiento circula por WhatsApp; hay que asumir que
        termina en manos de terceros, asi que los apellidos van iniciales.
        """
        parts = self.customer_name.split()
        if not parts:
            return ""
        return " ".join([parts[0], *(f"{p[0]}." for p in parts[1:])])


@dataclass(frozen=True, slots=True)
class DeliveryEvent:
    """Hecho ocurrido en terreno. Se escribe una vez y no se modifica."""

    id: int | None
    stop_id: int
    driver_id: int
    client_event_id: UUID
    kind: EventKind
    occurred_at: datetime
    reason: FailureReason | None = None
    note: str = ""
    coordinates: Coordinates | None = None
    received_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.kind is EventKind.FAILED and self.reason is None:
            raise ValueError("una entrega fallida necesita motivo")

    @property
    def offline_lag_seconds(self) -> float | None:
        """Cuanto tardo el hecho en llegar. Mide la salud del sync offline."""
        if self.received_at is None:
            return None
        return (self.received_at - self.occurred_at).total_seconds()


@dataclass(frozen=True, slots=True)
class LocationPing:
    driver_id: int
    coordinates: Coordinates
    recorded_at: datetime
    accuracy_m: float | None = None
    speed_kmh: float | None = None


@dataclass(frozen=True, slots=True)
class RouteStop:
    stop_id: int
    sequence: int
    leg_distance_km: float
    eta_minutes: float
    stop: Stop | None = None


@dataclass(frozen=True, slots=True)
class Route:
    id: int | None
    depot_id: int
    vehicle_id: int
    date: date
    driver_id: int | None = None
    status: RouteStatus = RouteStatus.DRAFT
    planned_distance_km: float = 0.0
    planned_duration_minutes: float = 0.0
    planned_load: float = 0.0
    optimizer_metrics: dict = field(default_factory=dict)
    stops: tuple[RouteStop, ...] = ()
    vehicle_code: str = ""
    driver_name: str = ""
    stop_count: int = 0
