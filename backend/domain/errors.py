"""Errores de negocio.

Son del dominio, no de HTTP: el caso de uso no sabe que existe un 409. La capa
de entrega los traduce a codigos de estado.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base de todo lo que el negocio rechaza."""


class PlanningError(DomainError):
    """El dia no se puede planificar con los datos actuales."""


class StopNotFoundError(DomainError):
    """No existe una parada con ese identificador o codigo."""


class StopNotAssignedToDriverError(DomainError):
    """El chofer intento reportar sobre una parada que no es suya."""

    def __init__(self, stop_ids: list[int]) -> None:
        self.stop_ids = stop_ids
        super().__init__("Hay paradas que no pertenecen a tus rutas.")


class DeliveredStopCannotBeDeletedError(DomainError):
    """Una entrega hecha es parte del historial y no se borra."""
