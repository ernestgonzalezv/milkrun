"""Alta, consulta y baja de paradas: el catalogo que maneja la oficina."""

from __future__ import annotations

from dataclasses import replace

from ..entities import Stop
from ..errors import DeliveredStopCannotBeDeletedError, StopNotFoundError
from ..ports import Page, StopFilters, StopRepository
from ..values import StopStatus, new_tracking_code


class ListStops:
    def __init__(self, stops: StopRepository) -> None:
        self._stops = stops

    def __call__(self, filters: StopFilters) -> Page[Stop]:
        return self._stops.list(filters)


class GetStop:
    def __init__(self, stops: StopRepository) -> None:
        self._stops = stops

    def __call__(self, stop_id: int) -> Stop:
        stop = self._stops.get(stop_id)
        if stop is None:
            raise StopNotFoundError(str(stop_id))
        return stop


class CreateStop:
    def __init__(self, stops: StopRepository) -> None:
        self._stops = stops

    def __call__(self, stop: Stop) -> Stop:
        """El codigo de seguimiento lo asigna el dominio, nunca el cliente."""
        return self._stops.add(replace(stop, tracking_code=new_tracking_code()))


class UpdateStop:
    def __init__(self, stops: StopRepository) -> None:
        self._stops = stops

    def __call__(self, stop: Stop) -> Stop:
        if self._stops.get(stop.id) is None:
            raise StopNotFoundError(str(stop.id))
        return self._stops.replace(stop)


class DeleteStop:
    def __init__(self, stops: StopRepository) -> None:
        self._stops = stops

    def __call__(self, stop_id: int) -> None:
        stop = self._stops.get(stop_id)
        if stop is None:
            raise StopNotFoundError(str(stop_id))
        if stop.status is StopStatus.DELIVERED:
            raise DeliveredStopCannotBeDeletedError("Una parada entregada no se puede borrar.")
        self._stops.delete(stop_id)
