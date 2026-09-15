"""Controladores de entrega.

Cada vista hace tres cosas y ninguna mas: validar la entrada, invocar un caso
de uso y serializar la salida. No hay reglas de negocio ni consultas al ORM en
este archivo.
"""

from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDispatcher, IsDriver
from apps.shared.http import limit_offset, paginated
from config import container
from domain.ports import StopFilters
from domain.values import StopStatus

from .serializers import (
    EventBatchSerializer,
    PingBatchSerializer,
    PublicTrackingSerializer,
    StopSerializer,
)


@extend_schema(tags=["Deliveries"])
class StopListView(APIView):
    """Listado y alta de paradas."""

    def get_permissions(self):
        return [IsDispatcher()] if self.request.method == "POST" else super().get_permissions()

    @extend_schema(responses={200: StopSerializer(many=True)})
    def get(self, request):
        limit, offset = limit_offset(request)
        page = container.list_stops()(
            StopFilters(
                depot_id=_int_param(request, "depot"),
                scheduled_date=request.query_params.get("scheduled_date") or None,
                status=_status_param(request),
                limit=limit,
                offset=offset,
            )
        )
        return paginated(page, StopSerializer, request, limit=limit, offset=offset)

    @extend_schema(request=StopSerializer, responses={201: StopSerializer})
    def post(self, request):
        serializer = StopSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = container.create_stop()(
            serializer.to_entity(today=container.clock().today())
        )
        return Response(StopSerializer(created).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Deliveries"])
class StopDetailView(APIView):
    """Consulta, edicion y baja de una parada."""

    def get_permissions(self):
        write = self.request.method in ("PUT", "PATCH", "DELETE")
        return [IsDispatcher()] if write else super().get_permissions()

    @extend_schema(responses={200: StopSerializer})
    def get(self, request, pk: int):
        return Response(StopSerializer(container.get_stop()(pk)).data)

    @extend_schema(request=StopSerializer, responses={200: StopSerializer})
    def patch(self, request, pk: int):
        current = container.get_stop()(pk)
        merged = {**StopSerializer(current).data, **request.data}
        serializer = StopSerializer(data=merged)
        serializer.is_valid(raise_exception=True)
        updated = container.update_stop()(
            serializer.to_entity(stop_id=pk, today=current.scheduled_date)
        )
        return Response(StopSerializer(updated).data)

    put = patch

    @extend_schema(responses={204: OpenApiResponse(description="Stop deleted")})
    def delete(self, request, pk: int):
        container.delete_stop()(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Driver app"],
    summary="Sync the driver event queue",
    description=(
        "Idempotent on `client_event_id`. Resending the same batch duplicates nothing: "
        "events already seen are reported under `duplicates` and the response stays "
        "200, so the app can clear its queue without ambiguity."
    ),
    request=EventBatchSerializer,
    responses={200: OpenApiResponse(description="Summary of what the sync stored")},
    examples=[
        OpenApiExample(
            "A delivery and a failure in one batch",
            value={
                "events": [
                    {
                        "stop": 12,
                        "client_event_id": "6f1a5c1e-8f0b-4a5e-9d33-2f2f0f6a1b01",
                        "kind": "delivered",
                        "occurred_at": "2026-09-12T14:02:11Z",
                    },
                    {
                        "stop": 13,
                        "client_event_id": "6f1a5c1e-8f0b-4a5e-9d33-2f2f0f6a1b02",
                        "kind": "failed",
                        "reason": "absent",
                        "note": "Knocked three times, nobody answered",
                        "occurred_at": "2026-09-12T14:31:47Z",
                    },
                ]
            },
            request_only=True,
        )
    ],
)
class EventSyncView(APIView):
    permission_classes = (IsDriver,)

    def post(self, request):
        serializer = EventBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = container.sync_driver_events()(
            request.user.id, serializer.to_entities(request.user.id)
        )
        return Response(
            {
                "created": report.created,
                "duplicates": report.duplicates,
                "rejected": report.rejected,
                "duplicate_ids": list(report.duplicate_ids),
                "server_time": container.clock().now(),
            }
        )


@extend_schema(
    tags=["Driver app"],
    summary="Upload buffered GPS positions",
    request=PingBatchSerializer,
    responses={202: OpenApiResponse(description="Number of new positions stored")},
)
class PingSyncView(APIView):
    permission_classes = (IsDriver,)

    def post(self, request):
        serializer = PingBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = container.sync_driver_pings()(serializer.to_entities(request.user.id))
        return Response({"created": created}, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    tags=["Public tracking"],
    summary="Public tracking for one shipment",
    description="No authentication. Limited to 60 requests per minute per IP.",
    responses={200: PublicTrackingSerializer},
)
class PublicTrackingView(APIView):
    """Lo que abre el cliente desde el enlace que le mandaron."""

    permission_classes = (AllowAny,)
    authentication_classes = ()
    throttle_scope = "tracking"

    def get(self, request, code: str):
        shipment = container.track_shipment()(code)
        return Response(PublicTrackingSerializer(shipment).data)


def _int_param(request, name: str) -> int | None:
    raw = request.query_params.get(name)
    return int(raw) if raw and raw.isdigit() else None


def _status_param(request) -> StopStatus | None:
    raw = request.query_params.get("status")
    return StopStatus(raw) if raw in StopStatus._value2member_map_ else None
