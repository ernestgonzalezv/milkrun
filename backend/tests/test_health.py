"""Las sondas de salud.

Se prueban porque son justo lo que nadie mira hasta que el despliegue entra en
bucle de reinicios, y entonces son lo unico que importa.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_responde_ok_sin_autenticacion(client):
    respuesta = client.get(reverse("healthz"))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readyz_confirma_que_la_base_responde(client):
    respuesta = client.get(reverse("readyz"))

    assert respuesta.status_code == 200
    assert respuesta.json()["database"] == "ok"


@pytest.mark.django_db
def test_readyz_devuelve_503_si_la_base_falla(client):
    with patch("apps.shared.health.connection.cursor", side_effect=RuntimeError("caida")):
        respuesta = client.get(reverse("readyz"))

    assert respuesta.status_code == 503
    assert respuesta.json()["status"] == "error"


@pytest.mark.django_db
def test_readyz_no_filtra_el_error_real(client):
    """El detalle de psycopg lleva host, puerto y usuario. No puede salir."""
    with patch("apps.shared.health.connection.cursor", side_effect=RuntimeError("host=secreto")):
        respuesta = client.get(reverse("readyz"))

    assert "secreto" not in respuesta.content.decode()
