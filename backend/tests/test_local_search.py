"""2-opt y Or-opt: nunca empeoran y nunca pierden paradas."""

from __future__ import annotations

from itertools import permutations

import pytest

from optimizer.geo import DistanceMatrix, Point
from optimizer.local_search import or_opt, refine, two_opt

from .factories import HABANA, random_stops

DEPOT = 0


def _matriz(stops):
    return DistanceMatrix([HABANA, *(s.point for s in stops)], detour_factor=1.0)


def _km(ruta, matriz):
    return matriz.path_km([DEPOT, *ruta, DEPOT])


@pytest.mark.parametrize("mejora", [two_opt, or_opt, refine])
@pytest.mark.parametrize("seed", [1, 2, 3, 17, 42])
def test_la_mejora_local_nunca_alarga_la_ruta(mejora, seed):
    stops = random_stops(14, seed=seed)
    matriz = _matriz(stops)
    original = list(range(1, len(stops) + 1))

    mejorada = mejora(original, matriz)

    assert _km(mejorada, matriz) <= _km(original, matriz) + 1e-9


@pytest.mark.parametrize("mejora", [two_opt, or_opt, refine])
@pytest.mark.parametrize("seed", [1, 2, 3, 17, 42])
def test_la_mejora_local_conserva_exactamente_las_mismas_paradas(mejora, seed):
    stops = random_stops(14, seed=seed)
    matriz = _matriz(stops)
    original = list(range(1, len(stops) + 1))

    mejorada = mejora(original, matriz)

    assert sorted(mejorada) == sorted(original)
    assert len(mejorada) == len(set(mejorada))


def test_two_opt_deshace_un_cruce_conocido():
    """Cuatro esquinas de un cuadrado visitadas en diagonal: la ruta se cruza.

        A---B      recorrido dado: deposito -> B -> A -> C -> D
        |   |      2-opt tiene que devolver un perimetro, que es lo optimo.
        D---C

    Con 4 paradas el optimo se calcula por fuerza bruta (24 permutaciones),
    asi que la comparacion es contra el valor exacto, no contra una intuicion.
    """
    esquinas = [Point(0.00, 0.00), Point(0.00, 0.02), Point(0.02, 0.02), Point(0.02, 0.00)]
    matriz = DistanceMatrix([Point(-0.01, 0.01), *esquinas], detour_factor=1.0)
    cruzada = [2, 1, 3, 4]
    optimo = min(_km(list(p), matriz) for p in permutations([1, 2, 3, 4]))

    recta = two_opt(cruzada, matriz)

    assert _km(recta, matriz) < _km(cruzada, matriz)
    assert _km(recta, matriz) == pytest.approx(optimo)


@pytest.mark.parametrize("seed", [4, 8, 15, 16, 23, 42])
def test_refine_alcanza_el_optimo_en_instancias_de_siete_paradas(seed):
    """Contra fuerza bruta: con 7 paradas son 5040 recorridos, se puede.

    No es una garantia teorica (2-opt no es exacto), es una cota empirica que
    avisa si una refactorizacion degrada la calidad de la busqueda local.
    """
    stops = random_stops(7, seed=seed)
    matriz = _matriz(stops)
    indices = list(range(1, 8))
    optimo = min(_km(list(p), matriz) for p in permutations(indices))

    resultado = _km(refine(indices, matriz), matriz)

    assert resultado <= optimo * 1.02


def test_rutas_de_una_o_dos_paradas_se_devuelven_intactas():
    stops = random_stops(2, seed=5)
    matriz = _matriz(stops)
    assert two_opt([1], matriz) == [1]
    assert two_opt([1, 2], matriz) == [1, 2]
    assert or_opt([1], matriz) == [1]


def test_refine_es_determinista():
    stops = random_stops(20, seed=11)
    matriz = _matriz(stops)
    entrada = list(range(1, 21))
    assert refine(entrada, matriz) == refine(entrada, matriz)


def test_refine_no_muta_la_entrada():
    stops = random_stops(12, seed=3)
    matriz = _matriz(stops)
    entrada = list(range(1, 13))
    copia = list(entrada)

    refine(entrada, matriz)

    assert entrada == copia
