"""Serializers de ruteo, sobre entidades del dominio."""

from __future__ import annotations

from rest_framework import serializers

from apps.deliveries.serializers import StopSerializer


class RouteStopSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="stop_id", read_only=True)
    sequence = serializers.IntegerField(read_only=True)
    leg_distance_km = serializers.FloatField(read_only=True)
    eta_minutes = serializers.FloatField(read_only=True)
    stop = StopSerializer(read_only=True)


class RouteSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    depot = serializers.IntegerField(source="depot_id", read_only=True)
    date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    vehicle = serializers.IntegerField(source="vehicle_id", read_only=True)
    vehicle_code = serializers.CharField(read_only=True)
    driver = serializers.IntegerField(source="driver_id", read_only=True, allow_null=True)
    driver_name = serializers.CharField(read_only=True)
    planned_distance_km = serializers.FloatField(read_only=True)
    planned_duration_minutes = serializers.FloatField(read_only=True)
    planned_load = serializers.FloatField(read_only=True)
    optimizer_metrics = serializers.JSONField(read_only=True)
    stops = RouteStopSerializer(many=True, read_only=True)


class RouteSummarySerializer(serializers.Serializer):
    """Version liviana para listados: sin las paradas anidadas."""

    id = serializers.IntegerField(read_only=True)
    date = serializers.DateField(read_only=True)
    status = serializers.CharField(read_only=True)
    vehicle_code = serializers.CharField(read_only=True)
    driver_name = serializers.CharField(read_only=True)
    planned_distance_km = serializers.FloatField(read_only=True)
    planned_duration_minutes = serializers.FloatField(read_only=True)
    stop_count = serializers.IntegerField(read_only=True)


class PlanRequestSerializer(serializers.Serializer):
    depot = serializers.IntegerField(help_text="Id del deposito a planificar.")
    date = serializers.DateField(help_text="Fecha de reparto (YYYY-MM-DD).")
    replan = serializers.BooleanField(
        default=False, help_text="Rehacer el plan si ya existe uno para ese dia."
    )
