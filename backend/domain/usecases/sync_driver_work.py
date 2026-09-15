"""Recibir la cola offline de la app movil."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..entities import DeliveryEvent, LocationPing
from ..errors import StopNotAssignedToDriverError
from ..policies import project_status
from ..ports import EventRepository, PingRepository, StopRepository, UnitOfWork

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SyncReport:
    created: int = 0
    duplicates: int = 0
    rejected: int = 0
    duplicate_ids: tuple[str, ...] = field(default_factory=tuple)


class SyncDriverEvents:
    """Guarda una tanda de hechos de forma idempotente.

    Un reenvio de la misma cola no crea duplicados ni devuelve error: la
    restriccion unica sobre (chofer, client_event_id) hace el trabajo y aqui
    solo se cuenta. Es lo que permite que la app aplique la politica mas
    simple posible —reintentar hasta 2xx— sin logica de reconciliacion.
    """

    def __init__(
        self,
        events: EventRepository,
        stops: StopRepository,
        uow: UnitOfWork,
    ) -> None:
        self._events = events
        self._stops = stops
        self._uow = uow

    def __call__(self, driver_id: int, batch: Sequence[DeliveryEvent]) -> SyncReport:
        assigned = self._stops.ids_assigned_to_driver(driver_id)
        foreign = sorted({e.stop_id for e in batch} - assigned)
        if foreign:
            raise StopNotAssignedToDriverError(foreign)

        created: list[DeliveryEvent] = []
        duplicates: list[str] = []

        with self._uow.atomic():
            for event in batch:
                stored = self._events.append(event)
                if stored is None:
                    duplicates.append(str(event.client_event_id))
                    continue
                created.append(stored)

            for stop_id in {e.stop_id for e in created}:
                self._refresh_status(stop_id)

        logger.info(
            "sync del chofer %s: %d nuevos, %d duplicados",
            driver_id, len(created), len(duplicates),
        )
        return SyncReport(
            created=len(created),
            duplicates=len(duplicates),
            duplicate_ids=tuple(duplicates),
        )

    def _refresh_status(self, stop_id: int) -> None:
        stop = self._stops.get(stop_id)
        if stop is None:
            return
        projected = project_status(
            stop,
            self._events.for_stop(stop_id),
            is_planned=self._stops.is_planned(stop_id),
        )
        if projected is not stop.status:
            self._stops.set_status([stop_id], projected)


class SyncDriverPings:
    """Guarda posiciones GPS descartando reenvios."""

    def __init__(self, pings: PingRepository) -> None:
        self._pings = pings

    def __call__(self, batch: Sequence[LocationPing]) -> int:
        return self._pings.append_many(batch)
