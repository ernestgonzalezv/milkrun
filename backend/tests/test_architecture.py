"""La regla de dependencia, verificada.

Una convencion que solo vive en un documento se erosiona la primera tarde de
apuro. Estos tests fallan en su lugar. Si uno se pone rojo, se arregla el
codigo, nunca el test.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

BACKEND = pathlib.Path(__file__).resolve().parent.parent

PROHIBIDO_EN_DOMINIO = ("django", "rest_framework", "apps", "infrastructure", "config")
PROHIBIDO_EN_OPTIMIZER = ("django", "rest_framework", "apps", "domain", "infrastructure", "numpy")


def _modulos(paquete: str) -> list[pathlib.Path]:
    return sorted((BACKEND / paquete).rglob("*.py"))


def _vistas_con_negocio() -> list[pathlib.Path]:
    """Vistas sujetas a la regla, sin los catalogos de flota (ver ADR 0007)."""
    return [v for v in BACKEND.glob("apps/*/views.py") if "fleet" not in v.parts]


def _imports(archivo: pathlib.Path) -> set[str]:
    """Raices de los modulos importados, resolviendo los relativos a absoluto."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    raices: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            raices |= {alias.name.split(".")[0] for alias in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            raices.add(nodo.module.split(".")[0])
    return raices


@pytest.mark.parametrize("archivo", _modulos("domain"), ids=lambda p: p.name)
def test_el_dominio_no_conoce_el_framework_ni_los_adaptadores(archivo):
    prohibidos = _imports(archivo) & set(PROHIBIDO_EN_DOMINIO)

    assert not prohibidos, (
        f"{archivo.relative_to(BACKEND)} importa {sorted(prohibidos)}. "
        "El dominio no puede depender de la infraestructura: la flecha va al reves."
    )


@pytest.mark.parametrize("archivo", _modulos("optimizer"), ids=lambda p: p.name)
def test_el_optimizador_no_tiene_dependencias(archivo):
    prohibidos = _imports(archivo) & set(PROHIBIDO_EN_OPTIMIZER)

    assert not prohibidos, (
        f"{archivo.relative_to(BACKEND)} importa {sorted(prohibidos)}. "
        "El optimizador es Python puro; ver docs/adr/0004."
    )


@pytest.mark.parametrize(
    "archivo", _vistas_con_negocio(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_las_vistas_no_consultan_el_orm(archivo):
    """Toda consulta vive en un repositorio.

    Los ViewSets de catalogo de flota son la excepcion documentada en el ADR
    0007: son CRUD sobre datos de referencia, sin regla de negocio.
    """
    texto = archivo.read_text(encoding="utf-8")

    assert ".objects." not in texto, (
        f"{archivo.relative_to(BACKEND)} consulta el ORM. "
        "Las vistas invocan casos de uso; las consultas viven en infrastructure/."
    )


def test_los_casos_de_uso_no_se_llaman_entre_si():
    """Si dos comparten logica, esa logica baja al repositorio o a policies."""
    for archivo in _modulos("domain/usecases"):
        importa_otro_caso = {raiz for raiz in _imports(archivo) if raiz == "usecases"}
        assert not importa_otro_caso, f"{archivo.name} envuelve otro caso de uso"


def test_la_capa_de_entrega_no_importa_adaptadores_concretos():
    """Las vistas piden casos de uso al contenedor, no construyen dependencias."""
    for archivo in _modulos("apps"):
        if archivo.name != "views.py":
            continue
        assert "infrastructure" not in _imports(archivo), (
            f"{archivo.relative_to(BACKEND)} conoce un adaptador concreto; usa config.container."
        )
