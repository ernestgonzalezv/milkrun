"""Sondas de salud para el balanceador.

Son dos y la diferencia no es cosmetica:

    /healthz   liveness    "el proceso responde"       no toca la base
    /readyz    readiness   "puedo atender trafico"     comprueba la base

El ALB apunta a /healthz a proposito. Si apuntara a /readyz, una caida de RDS
tumbaria el health check de todas las tareas, ECS las mataria por no sanas, y
al volver la base no quedaria ninguna viva para atender: un incidente de la
base de datos se convertiria en una caida total del servicio.

/readyz existe para el operador y para un despliegue: ahi si quieres saber si
la tarea nueva puede de verdad hablar con la base antes de mandarle trafico.
"""

from __future__ import annotations

import logging

from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def healthz(_request: HttpRequest) -> JsonResponse:
    """Responde siempre 200 si el proceso esta vivo. Deliberadamente barato."""
    return JsonResponse({"status": "ok"})


def readyz(_request: HttpRequest) -> JsonResponse:
    """503 si la base no contesta.

    El motivo del fallo se registra pero no se devuelve: el mensaje de psycopg
    lleva host, puerto y usuario, y este endpoint no esta autenticado.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("readyz: la base de datos no responde")
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)

    return JsonResponse({"status": "ok", "database": "ok"})
