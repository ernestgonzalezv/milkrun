"""Reglas de negocio puras.

Aqui vive lo que decide el negocio, sin depender de como se guardan los datos.
"""

from __future__ import annotations

from collections.abc import Sequence

from .entities import DeliveryEvent, Stop
from .values import EventKind, StopStatus


def project_status(stop: Stop, events: Sequence[DeliveryEvent], is_planned: bool) -> StopStatus:
    """Deriva el estado de la parada a partir de su bitacora.

    Se recalcula desde cero en vez de ir mutando el estado evento a evento.
    Cuesta recorrer la lista y a cambio es correcto cuando los hechos llegan
    desordenados, que es exactamente lo que pasa con una cola offline: el
    chofer marca "entregada" en un sotano sin senal y ese evento llega despues
    del "sali hacia la proxima parada".
    """
    if stop.status is StopStatus.CANCELLED:
        return StopStatus.CANCELLED

    relevant = [e for e in events if e.kind is not EventKind.NOTE]
    if relevant:
        latest = max(relevant, key=lambda e: (e.occurred_at, e.id or 0))
        projected = latest.kind.projected_status
        if projected is not None:
            return projected

    return StopStatus.PLANNED if is_planned else StopStatus.PENDING
