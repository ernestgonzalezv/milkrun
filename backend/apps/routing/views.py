"""Controladores de ruteo: planificar el dia y consultar rutas."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsDispatcher, IsDriver
from apps.deliveries.serializers import StopSerializer
from apps.shared.http import limit_offset, paginated
from config import container
from domain.ports import RouteFilters
from domain.values import RouteStatus

from .serializers import PlanRequestSerializer, RouteSerializer, RouteSummarySerializer


@extend_schema(
    tags=["Planning"],
    parameters=[
        OpenApiParameter(
            name="expand",
            description=(
                "With `expand=stops` the list includes each route's stops. The dashboard "
                "map uses it, because it needs the whole day in one request. The default "
                "listing stays light."
            ),
            required=False,
            type=str,
            enum=["stops"],
        )
    ],
    responses={200: RouteSummarySerializer(many=True)},
)
class RouteListView(APIView):
    """Consulta de rutas planificadas. Solo lectura: se crean planificando."""

    permission_classes = (IsDispatcher,)

    def get(self, request):
        limit, offset = limit_offset(request)
        expanded = request.query_params.get("expand") == "stops"

        page = container.routes_repository().list(
            RouteFilters(
                depot_id=_int_param(request, "depot"),
                date=request.query_params.get("date") or None,
                status=_status_param(request),
                driver_id=_int_param(request, "driver"),
                with_stops=expanded,
                limit=limit,
                offset=offset,
            )
        )
        serializer = RouteSerializer if expanded else RouteSummarySerializer
        return paginated(page, serializer, request, limit=limit, offset=offset)


@extend_schema(tags=["Planning"], responses={200: RouteSerializer})
class RouteDetailView(APIView):
    permission_classes = (IsDispatcher,)

    def get(self, request, pk: int):
        route = container.routes_repository().get(pk)
        if route is None:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RouteSerializer(route).data)


@extend_schema(
    tags=["Planning"],
    summary="Plan a depot's routes for one day",
    request=PlanRequestSerializer,
    responses={
        201: RouteSerializer(many=True),
        409: OpenApiResponse(description="A plan already exists and no re-plan was requested"),
    },
)
class PlanDayView(APIView):
    """Dispara el optimizador y persiste el plan resultante."""

    permission_classes = (IsDispatcher,)
    throttle_scope = "planning"

    def post(self, request):
        serializer = PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = container.plan_day()(data["depot"], data["date"], replan=data["replan"])

        return Response(
            {
                "routes": RouteSerializer(result.routes, many=True).data,
                "unassigned": StopSerializer(result.unassigned, many=True).data,
                "metrics": result.metrics,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Driver app"],
    summary="The signed-in driver's route for the day",
    description="Returns 204 when the driver has no route assigned for that date.",
    responses={200: RouteSerializer, 204: OpenApiResponse(description="No route assigned")},
)
class MyRouteView(APIView):
    """Lo primero que pide la app movil al abrir."""

    permission_classes = (IsDriver,)

    def get(self, request):
        day = request.query_params.get("date") or None
        route = container.get_driver_route()(request.user.id, day)
        if route is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(RouteSerializer(route).data)


def _int_param(request, name: str) -> int | None:
    raw = request.query_params.get(name)
    return int(raw) if raw and raw.isdigit() else None


def _status_param(request) -> RouteStatus | None:
    raw = request.query_params.get("status")
    return RouteStatus(raw) if raw in RouteStatus._value2member_map_ else None
