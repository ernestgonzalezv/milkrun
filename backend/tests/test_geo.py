"""Distancias y matriz de costos."""

import math

import pytest

from optimizer.geo import DistanceMatrix, Point, haversine_km

# Distancias conocidas, verificadas contra la formula de referencia.
HABANA_VIEJA = Point(23.1136, -82.3666)
VEDADO = Point(23.1367, -82.3861)
SANTIAGO = Point(20.0247, -75.8219)


def test_haversine_coincide_con_valores_conocidos():
    assert haversine_km(HABANA_VIEJA, VEDADO) == pytest.approx(3.25, abs=0.02)
    assert haversine_km(HABANA_VIEJA, SANTIAGO) == pytest.approx(758.8, abs=1.0)


def test_haversine_es_simetrica_y_nula_en_el_mismo_punto():
    assert haversine_km(HABANA_VIEJA, VEDADO) == haversine_km(VEDADO, HABANA_VIEJA)
    assert haversine_km(VEDADO, VEDADO) == 0.0


def test_point_rechaza_coordenadas_invalidas():
    with pytest.raises(ValueError, match="latitud"):
        Point(91.0, 0.0)
    with pytest.raises(ValueError, match="longitud"):
        Point(0.0, -181.0)


def test_point_es_inmutable():
    p = Point(1.0, 2.0)
    with pytest.raises(AttributeError):
        p.lat = 5.0  # type: ignore[misc]


def test_matriz_es_simetrica_con_diagonal_cero():
    puntos = [HABANA_VIEJA, VEDADO, SANTIAGO, Point(22.0, -80.0)]
    m = DistanceMatrix(puntos, detour_factor=1.0)
    for i in range(len(puntos)):
        assert m(i, i) == 0.0
        for j in range(len(puntos)):
            assert m(i, j) == m(j, i)


def test_matriz_cumple_desigualdad_triangular():
    puntos = [HABANA_VIEJA, VEDADO, SANTIAGO]
    m = DistanceMatrix(puntos, detour_factor=1.0)
    assert m(0, 2) <= m(0, 1) + m(1, 2) + 1e-9


def test_factor_de_rodeo_escala_linealmente():
    puntos = [HABANA_VIEJA, VEDADO]
    recta = DistanceMatrix(puntos, detour_factor=1.0)(0, 1)
    con_rodeo = DistanceMatrix(puntos, detour_factor=1.4)(0, 1)
    assert con_rodeo == pytest.approx(recta * 1.4)


def test_factor_de_rodeo_menor_que_uno_es_un_error():
    with pytest.raises(ValueError, match="rodeo"):
        DistanceMatrix([HABANA_VIEJA, VEDADO], detour_factor=0.8)


def test_path_km_suma_los_tramos():
    puntos = [HABANA_VIEJA, VEDADO, SANTIAGO]
    m = DistanceMatrix(puntos, detour_factor=1.0)
    assert m.path_km([0, 1, 2, 0]) == pytest.approx(m(0, 1) + m(1, 2) + m(2, 0))


def test_matriz_usa_memoria_triangular():
    """Solo se guarda el triangulo inferior: n(n-1)/2 valores, no n^2."""
    n = 50
    m = DistanceMatrix([Point(i * 0.01, 0.0) for i in range(n)])
    assert len(m._data) == n * (n - 1) // 2
    assert math.isclose(m(49, 0), m(0, 49))
