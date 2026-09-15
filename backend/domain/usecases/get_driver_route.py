"""Consultar la ruta del chofer autenticado."""

from __future__ import annotations

from datetime import date

from ..entities import Route
from ..ports import Clock, RouteRepository


class GetDriverRoute:
    def __init__(self, routes: RouteRepository, clock: Clock) -> None:
        self._routes = routes
        self._clock = clock

    def __call__(self, driver_id: int, day: date | None = None) -> Route | None:
        """Devuelve `None` cuando el chofer no tiene ruta ese dia.

        No tener ruta no es un error, y la app movil necesita distinguirlo de
        un fallo de red: por eso el caso de uso devuelve `None` y no lanza.
        """
        return self._routes.for_driver(driver_id, day or self._clock.today())
