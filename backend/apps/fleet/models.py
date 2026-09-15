"""Depositos y vehiculos."""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

LAT_VALIDATORS = [MinValueValidator(-90), MaxValueValidator(90)]
LON_VALIDATORS = [MinValueValidator(-180), MaxValueValidator(180)]


class Depot(models.Model):
    """Punto de salida y regreso de los vehiculos."""

    name = models.CharField(_("name"), max_length=120, unique=True)
    address = models.CharField(_("address"), max_length=255, blank=True)
    latitude = models.FloatField(_("latitude"), validators=LAT_VALIDATORS)
    longitude = models.FloatField(_("longitude"), validators=LON_VALIDATORS)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("depot")
        verbose_name_plural = _("depots")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Vehicle(models.Model):
    """Camion o moto disponible para repartir."""

    depot = models.ForeignKey(
        Depot, on_delete=models.CASCADE, related_name="vehicles", verbose_name=_("depot")
    )
    code = models.CharField(_("code"), max_length=32, unique=True)
    plate = models.CharField(_("plate"), max_length=16, blank=True)
    capacity = models.FloatField(
        _("capacity"),
        validators=[MinValueValidator(0.1)],
        help_text=_("In the same unit as the stops' demand."),
    )
    max_shift_minutes = models.PositiveIntegerField(_("max shift (min)"), default=480)
    avg_speed_kmh = models.FloatField(_("average speed (km/h)"), default=25.0)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("vehicle")
        verbose_name_plural = _("vehicles")
        ordering = ("code",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0), name="vehicle_capacity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(avg_speed_kmh__gt=0), name="vehicle_speed_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.plate})" if self.plate else self.code


class DriverProfile(models.Model):
    """Datos operativos del chofer, separados de la cuenta de usuario."""

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="driver_profile",
        verbose_name=_("user"),
    )
    depot = models.ForeignKey(
        Depot, on_delete=models.PROTECT, related_name="drivers", verbose_name=_("depot")
    )
    default_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_drivers",
        verbose_name=_("default vehicle"),
    )
    license_number = models.CharField(_("licence"), max_length=32, blank=True)
    is_available = models.BooleanField(_("available"), default=True)

    class Meta:
        verbose_name = _("driver")
        verbose_name_plural = _("drivers")
        ordering = ("user__username",)

    def __str__(self) -> str:
        return str(self.user)
