"""Piezas compartidas de la capa de entrega.

Traducen entre el mundo del dominio (entidades, errores de negocio) y el de
HTTP (codigos de estado, sobres de paginacion). El dominio no sabe que existe
un 409; esa traduccion vive aqui.
"""

from __future__ import annotations

from urllib.parse import urlencode

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from domain.errors import (
    DeliveredStopCannotBeDeletedError,
    DomainError,
    PlanningError,
    StopNotAssignedToDriverError,
    StopNotFoundError,
)
from domain.ports import Page

DOMAIN_STATUS = {
    PlanningError: status.HTTP_409_CONFLICT,
    StopNotFoundError: status.HTTP_404_NOT_FOUND,
    StopNotAssignedToDriverError: status.HTTP_403_FORBIDDEN,
    DeliveredStopCannotBeDeletedError: status.HTTP_400_BAD_REQUEST,
}


def domain_exception_handler(exc, context):
    """Convierte errores de dominio en respuestas, sin `try` en cada vista."""
    if isinstance(exc, DomainError):
        body = {"detail": str(exc)}
        if isinstance(exc, StopNotAssignedToDriverError):
            body["stops"] = exc.stop_ids
        return Response(body, status=DOMAIN_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST))
    return drf_exception_handler(exc, context)


def paginated(page: Page, serializer_class, request, *, limit: int, offset: int) -> Response:
    """Mismo sobre que produce LimitOffsetPagination de DRF.

    Se arma a mano porque la paginacion ocurre en el repositorio, sobre el
    queryset, y lo que llega aqui ya son entidades: DRF no puede paginar algo
    que ya viene paginado sin volver a tocar la base.
    """
    return Response(
        {
            "count": page.total,
            "next": _neighbour(request, limit, offset + limit, page.total),
            "previous": _neighbour(request, limit, offset - limit, page.total),
            "results": serializer_class(page.items, many=True).data,
        }
    )


def _neighbour(request, limit: int, offset: int, total: int) -> str | None:
    if offset < 0 or offset >= total:
        return None
    params = request.query_params.copy()
    params["limit"] = limit
    params["offset"] = offset
    return f"{request.build_absolute_uri(request.path)}?{urlencode(params, doseq=True)}"


def limit_offset(request, *, default_limit: int = 50, max_limit: int = 500) -> tuple[int, int]:
    limit = _positive_int(request.query_params.get("limit"), default_limit)
    offset = _positive_int(request.query_params.get("offset"), 0)
    return min(limit, max_limit), offset


def _positive_int(raw: str | None, fallback: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return value if value >= 0 else fallback
