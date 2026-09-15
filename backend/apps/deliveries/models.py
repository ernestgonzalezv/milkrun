"""Paradas de entrega y su bitacora de eventos.

Decision central del modulo: el estado de una parada NO se edita. Se escriben
eventos en una bitacora append-only y `Stop.status` es una proyeccion de esa
bitacora. Ver docs/adr/0002-bitacora-append-only.md.

Consecuencias practicas:
  - la app movil puede reenviar la misma cola sin miedo a duplicar nada
  - se puede reconstruir "que sabia el sistema a las 3pm" para un reclamo
  - un bug en la proyeccion se arregla y se recalcula; los hechos no se pierden
"""

from __future__ import annotations

import secrets

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.fleet.models import LAT_VALIDATORS, LON_VALIDATORS

TRACKING_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin O/0 ni I/1/L
TRACKING_LENGTH = 8


def generate_tracking_code() -> str:
    """Codigo publico de seguimiento, legible por telefono."""
    return "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(TRACKING_LENGTH))


class StopStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    PLANNED = "planned", _("Planned")
    IN_TRANSIT = "in_transit", _("In transit")
    DELIVERED = "delivered", _("Delivered")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")

    @classmethod
    def terminal(cls) -> set[str]:
        return {cls.DELIVERED, cls.FAILED, cls.CANCELLED}


class EventKind(models.TextChoices):
    DEPARTED = "departed", _("Departed for the stop")
    ARRIVED = "arrived", _("Arrived at the stop")
    DELIVERED = "delivered", _("Delivered")
    FAILED = "failed", _("Delivery failed")
    NOTE = "note", _("Note")


#: Como cada tipo de evento afecta al estado proyectado de la parada.
#: `None` significa "queda registrado pero no cambia el estado".
STATUS_PROJECTION: dict[str, str | None] = {
    EventKind.DEPARTED: StopStatus.IN_TRANSIT,
    EventKind.ARRIVED: StopStatus.IN_TRANSIT,
    EventKind.DELIVERED: StopStatus.DELIVERED,
    EventKind.FAILED: StopStatus.FAILED,
    EventKind.NOTE: None,
}


class FailureReason(models.TextChoices):
    ABSENT = "absent", _("Customer not there")
    WRONG_ADDRESS = "wrong_address", _("Wrong address")
    REFUSED = "refused", _("Order refused")
    NO_ACCESS = "no_access", _("No access to the site")
    OTHER = "other", _("Other")


class Stop(models.Model):
    """Un pedido a entregar en una direccion y una fecha."""

    tracking_code = models.CharField(
        _("tracking code"),
        max_length=16,
        unique=True,
        default=generate_tracking_code,
        editable=False,
    )
    depot = models.ForeignKey(
        "fleet.Depot", on_delete=models.PROTECT, related_name="stops", verbose_name=_("depot")
    )
    customer_name = models.CharField(_("customer"), max_length=120)
    phone = models.CharField(_("phone"), max_length=32, blank=True)
    address = models.CharField(_("address"), max_length=255)
    latitude = models.FloatField(_("latitude"), validators=LAT_VALIDATORS)
    longitude = models.FloatField(_("longitude"), validators=LON_VALIDATORS)
    demand = models.FloatField(
        _("demand"), default=1.0, validators=[MinValueValidator(0)],
        help_text=_("Weight or volume, in the same unit as the vehicle capacity."),
    )
    service_minutes = models.PositiveIntegerField(_("service time (min)"), default=5)
    scheduled_date = models.DateField(_("scheduled date"), default=timezone.localdate)
    status = models.CharField(
        _("status"), max_length=16, choices=StopStatus.choices,
        default=StopStatus.PENDING, editable=False,
        help_text=_("Projection of the event log. Never edited by hand."),
    )
    notes = models.TextField(_("notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("stop")
        verbose_name_plural = _("stops")
        ordering = ("scheduled_date", "created_at")
        indexes = [
            # El dashboard siempre filtra por deposito + fecha + estado.
            models.Index(fields=("depot", "scheduled_date", "status"), name="stop_planning_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.tracking_code} - {self.customer_name}"

    @property
    def is_open(self) -> bool:
        return self.status not in StopStatus.terminal()


class DeliveryEvent(models.Model):
    """Hecho ocurrido en terreno. Se escribe una vez y no se modifica.

    `client_event_id` lo genera la app movil antes de intentar enviar. Es lo
    que permite que la cola offline se reenvie N veces sin duplicar: la
    restriccion unica convierte el reintento en un no-op a nivel de base de
    datos, no en logica de aplicacion que se puede olvidar.
    """

    stop = models.ForeignKey(
        Stop, on_delete=models.CASCADE, related_name="events", verbose_name=_("stop")
    )
    driver = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="delivery_events",
        verbose_name=_("driver"),
    )
    client_event_id = models.UUIDField(
        _("client event id"),
        help_text=_("Generated by the mobile app; this is what makes resending idempotent."),
    )
    kind = models.CharField(_("kind"), max_length=16, choices=EventKind.choices)
    reason = models.CharField(
        _("reason"), max_length=24, choices=FailureReason.choices, blank=True
    )
    note = models.TextField(_("note"), blank=True)
    latitude = models.FloatField(_("latitude"), null=True, blank=True, validators=LAT_VALIDATORS)
    longitude = models.FloatField(_("longitude"), null=True, blank=True, validators=LON_VALIDATORS)
    occurred_at = models.DateTimeField(_("occurred at"), help_text=_("Device clock."))
    received_at = models.DateTimeField(_("received at"), auto_now_add=True)

    class Meta:
        verbose_name = _("delivery event")
        verbose_name_plural = _("delivery events")
        ordering = ("occurred_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("driver", "client_event_id"), name="event_idempotency_key"
            ),
            models.CheckConstraint(
                condition=~models.Q(kind="failed") | ~models.Q(reason=""),
                name="failed_event_requires_reason",
            ),
        ]
        indexes = [models.Index(fields=("stop", "occurred_at"), name="event_stop_time_idx")]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} @ {self.stop.tracking_code}"

    @property
    def offline_lag_seconds(self) -> float:
        """Cuanto tardo el evento en llegar. Mide la salud del sync offline."""
        return (self.received_at - self.occurred_at).total_seconds()


class LocationPing(models.Model):
    """Posicion del chofer. Alto volumen, escritura barata, sin relaciones caras."""

    driver = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="pings", verbose_name=_("driver")
    )
    latitude = models.FloatField(_("latitude"), validators=LAT_VALIDATORS)
    longitude = models.FloatField(_("longitude"), validators=LON_VALIDATORS)
    accuracy_m = models.FloatField(_("accuracy (m)"), null=True, blank=True)
    speed_kmh = models.FloatField(_("speed (km/h)"), null=True, blank=True)
    recorded_at = models.DateTimeField(_("recorded at"))

    class Meta:
        verbose_name = _("position")
        verbose_name_plural = _("positions")
        ordering = ("-recorded_at",)
        indexes = [models.Index(fields=("driver", "-recorded_at"), name="ping_driver_time_idx")]
        constraints = [
            # Dos pings del mismo chofer con el mismo timestamp son un reenvio.
            models.UniqueConstraint(
                fields=("driver", "recorded_at"), name="ping_dedup_by_timestamp"
            )
        ]

    def __str__(self) -> str:
        return f"{self.driver} @ {self.recorded_at:%H:%M:%S}"
