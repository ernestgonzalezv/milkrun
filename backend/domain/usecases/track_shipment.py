"""Seguimiento publico de un envio."""

from __future__ import annotations

from dataclasses import dataclass

from ..entities import DeliveryEvent, Stop
from ..errors import StopNotFoundError
from ..ports import EventRepository, StopRepository
from ..values import EventKind


@dataclass(frozen=True, slots=True)
class Shipment:
    stop: Stop
    timeline: tuple[DeliveryEvent, ...]


class TrackShipment:
    def __init__(self, stops: StopRepository, events: EventRepository) -> None:
        self._stops = stops
        self._events = events

    def __call__(self, tracking_code: str) -> Shipment:
        stop = self._stops.get_by_tracking_code(tracking_code)
        if stop is None:
            raise StopNotFoundError(tracking_code)

        timeline = tuple(
            event
            for event in sorted(self._events.for_stop(stop.id), key=lambda e: e.occurred_at)
            if event.kind is not EventKind.NOTE
        )
        return Shipment(stop=stop, timeline=timeline)
