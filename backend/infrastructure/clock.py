"""Reloj del sistema.

El dominio nunca llama a `timezone.now()` directamente: recibe este puerto,
y asi los tests pueden fijar la hora en vez de tolerar deriva.
"""

from __future__ import annotations

from datetime import date, datetime

from django.utils import timezone


class DjangoClock:
    def today(self) -> date:
        return timezone.localdate()

    def now(self) -> datetime:
        return timezone.now()
