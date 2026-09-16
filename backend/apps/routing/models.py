"""Rutas planificadas: la salida del optimizador, persistida."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class RouteStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    DISPATCHED = "dispatched", _("Dispatched")
    IN_PROGRESS = "in_progress", _("In progress")
    COMPLETED = "completed", _("Completed")


class Route(models.Model):
    """Plan de un vehiculo para un dia."""

    depot = models.ForeignKey(
        "fleet.Depot", on_delete=models.PROTECT, related_name="routes", verbose_name=_("depot")
    )
    vehicle = models.ForeignKey(
        "fleet.Vehicle",
        on_delete=models.PROTECT,
        related_name="routes",
        verbose_name=_("vehicle"),
    )
    driver = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routes",
        verbose_name=_("driver"),
    )
    date = models.DateField(_("date"))
    status = models.CharField(
        _("status"), max_length=16, choices=RouteStatus.choices, default=RouteStatus.DRAFT
    )
    planned_distance_km = models.FloatField(_("planned distance (km)"), default=0.0)
    planned_duration_minutes = models.FloatField(_("planned duration (min)"), default=0.0)
    planned_load = models.FloatField(_("planned load"), default=0.0)
    optimizer_metrics = models.JSONField(
        _("optimizer metrics"),
        default=dict,
        blank=True,
        help_text=_("Distance against the baselines and solve time, so the plan can be audited."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("route")
        verbose_name_plural = _("routes")
        ordering = ("-date", "vehicle__code")
        constraints = [
            models.UniqueConstraint(fields=("vehicle", "date"), name="one_route_per_vehicle_day")
        ]
        indexes = [models.Index(fields=("date", "status"), name="route_date_status_idx")]

    def __str__(self) -> str:
        return f"{self.vehicle} - {self.date:%d/%m/%Y}"


class RouteStop(models.Model):
    """Una parada dentro de una ruta, en su posicion de recorrido."""

    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="route_stops", verbose_name=_("route")
    )
    stop = models.ForeignKey(
        "deliveries.Stop",
        on_delete=models.CASCADE,
        related_name="route_stops",
        verbose_name=_("stop"),
    )
    sequence = models.PositiveIntegerField(_("sequence"))
    leg_distance_km = models.FloatField(
        _("leg distance (km)"),
        default=0.0,
        help_text=_("From the previous stop, or from the depot when it is the first."),
    )
    eta_minutes = models.FloatField(
        _("ETA (min from departure)"),
        default=0.0,
        help_text=_("The planner's estimate, not the real arrival time."),
    )

    class Meta:
        verbose_name = _("route stop")
        verbose_name_plural = _("route stops")
        ordering = ("route", "sequence")
        constraints = [
            models.UniqueConstraint(fields=("route", "sequence"), name="unique_sequence_per_route"),
            models.UniqueConstraint(fields=("route", "stop"), name="unique_stop_per_route"),
        ]

    def __str__(self) -> str:
        return f"{self.sequence}. {self.stop.customer_name}"
