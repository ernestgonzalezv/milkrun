"""Usuarios y roles.

Se define un User propio desde el dia uno aunque hoy solo agregue un campo:
cambiar AUTH_USER_MODEL sobre una base con datos es de las migraciones mas
dolorosas de Django, y hacerlo despues nunca sale gratis.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    DISPATCHER = "dispatcher", _("Dispatcher")
    DRIVER = "driver", _("Driver")


class User(AbstractUser):
    role = models.CharField(_("role"), max_length=16, choices=Role.choices, default=Role.DISPATCHER)
    phone = models.CharField(_("phone"), max_length=32, blank=True)

    class Meta(AbstractUser.Meta):
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def is_driver(self) -> bool:
        return self.role == Role.DRIVER

    @property
    def is_dispatcher(self) -> bool:
        return self.role == Role.DISPATCHER or self.is_superuser

    def __str__(self) -> str:
        return self.get_full_name() or self.username
