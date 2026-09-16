"""Compara el solver contra los baselines sobre instancias reproducibles.

    python -m optimizer.benchmark

Sirve para dos cosas: llenar la tabla del README con numeros que cualquiera
puede reproducir, y detectar regresiones de calidad al tocar el algoritmo.

Se miden dos regimenes porque el solver se comporta distinto en cada uno:

  - flota dimensionada: hay capacidad para toda la demanda. Es la operacion
    normal, y donde Clarke-Wright + 2-opt gana claro.
  - flota saturada: la capacidad cubre ~80% de la demanda. El problema pasa a
    ser *que* paradas servir, no en que orden, y la ventaja se estrecha.

Los baselines corren con la misma flota y las mismas restricciones. Como un
metodo peor puede terminar sirviendo menos paradas, la columna que manda es
km por parada entregada.

Con --referencia se anade una tabla contra OR-Tools, que es lo que se usaria
en un trabajo real. Va aparte y desactivada por defecto: `ortools` es
dependencia de desarrollo, tarda segundos por instancia, y responde una
pregunta distinta. Los baselines dicen "cuanto mejora esto la operacion
manual"; OR-Tools dice "cuanta calidad cuesta haberlo escrito a mano".
"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from .geo import DEFAULT_DETOUR_FACTOR, DistanceMatrix, Point
from .models import Fleet, Stop, Vehicle
from .reference import LIMITE_SEGUNDOS, disponible, ortools_reference
from .solver import solve

HABANA = Point(23.1136, -82.3666)

ESCENARIOS = [(25, 3), (50, 4), (100, 8), (200, 14), (400, 26)]
REPETICIONES = 5


def instancia(n: int, seed: int) -> tuple[Stop, ...]:
    rng = random.Random(seed)
    return tuple(
        Stop(
            id=f"S{i:04d}",
            point=Point(
                HABANA.lat + rng.uniform(-0.07, 0.07),
                HABANA.lon + rng.uniform(-0.10, 0.10),
            ),
            demand=rng.randint(1, 6),
            service_minutes=rng.choice([4.0, 6.0, 8.0]),
        )
        for i in range(n)
    )


def flota(stops: tuple[Stop, ...], vehiculos: int, cobertura: float) -> Fleet:
    """Flota cuya capacidad total es `cobertura` veces la demanda del dia."""
    capacidad = sum(s.demand for s in stops) * cobertura / vehiculos
    return Fleet(
        depot=HABANA,
        vehicles=tuple(
            Vehicle(f"V{k}", capacity=capacidad, max_shift_minutes=600.0) for k in range(vehiculos)
        ),
    )


def correr(n: int, vehiculos: int, cobertura: float, seed: int) -> dict[str, float]:
    stops = instancia(n, seed)
    fleet = flota(stops, vehiculos, cobertura)

    inicio = time.perf_counter()
    plan = solve(fleet, stops)
    ms = (time.perf_counter() - inicio) * 1000

    m = plan.metrics
    return {
        "km": m["total_km"],
        "servidas": m["stops_served"],
        "km_parada": m["km_per_stop"],
        "nn_km": m["baseline_nearest_neighbor_km"],
        "nn_servidas": m["baseline_nearest_neighbor_stops"],
        "seq_km": m["baseline_sequential_km"],
        "vs_nn": m["improvement_vs_nearest_neighbor_pct"],
        "vs_seq": m["improvement_vs_sequential_pct"],
        "ms": ms,
    }


def correr_con_referencia(
    n: int, vehiculos: int, cobertura: float, seed: int, limite: float
) -> dict[str, float]:
    """Misma instancia resuelta por los dos, para poder restar.

    La matriz se construye igual que dentro de `solve`: mismos puntos, mismo
    factor de rodeo. Si se construyera distinta, la diferencia de kilometros
    mediria la matriz y no el algoritmo.
    """
    stops = instancia(n, seed)
    fleet = flota(stops, vehiculos, cobertura)

    inicio = time.perf_counter()
    plan = solve(fleet, stops)
    ms_propio = (time.perf_counter() - inicio) * 1000

    matrix = DistanceMatrix([fleet.depot, *(s.point for s in stops)], DEFAULT_DETOUR_FACTOR)
    demands = {i + 1: s.demand for i, s in enumerate(stops)}
    service = {i + 1: s.service_minutes for i, s in enumerate(stops)}

    inicio = time.perf_counter()
    ref = ortools_reference(matrix, demands, service, fleet.vehicles, time_limit_seconds=limite)
    ms_ref = (time.perf_counter() - inicio) * 1000

    propio_km_parada = plan.metrics["km_per_stop"]
    brecha = (
        (propio_km_parada - ref.km_per_stop) / ref.km_per_stop * 100 if ref.km_per_stop > 0 else 0.0
    )

    return {
        "propio_km_parada": propio_km_parada,
        "propio_servidas": plan.metrics["stops_served"],
        "propio_ms": ms_propio,
        "ref_km_parada": ref.km_per_stop,
        "ref_servidas": ref.served,
        "ref_ms": ms_ref,
        "brecha": brecha,
    }


ENCABEZADO = (
    f"{'paradas':>8} {'veh':>4} | {'plan km':>8} {'serv':>5} {'km/par':>7} | "
    f"{'NN km':>8} {'serv':>5} | {'orden km':>9} | {'vs NN':>7} {'vs orden':>9} {'tiempo':>8}"
)


def tabla(titulo: str, cobertura: float, repeticiones: int) -> None:
    print(f"\n{titulo}\n")
    print(ENCABEZADO)
    print("-" * len(ENCABEZADO))
    for n, vehiculos in ESCENARIOS:
        corridas = [correr(n, vehiculos, cobertura, seed) for seed in range(repeticiones)]
        med = {k: statistics.mean(c[k] for c in corridas) for k in corridas[0]}
        print(
            f"{n:>8} {vehiculos:>4} | {med['km']:>8.0f} {med['servidas']:>5.0f} "
            f"{med['km_parada']:>7.2f} | {med['nn_km']:>8.0f} {med['nn_servidas']:>5.0f} | "
            f"{med['seq_km']:>9.0f} | {med['vs_nn']:>6.1f}% {med['vs_seq']:>8.1f}% "
            f"{med['ms']:>7.0f}ms"
        )


ENCABEZADO_REF = (
    f"{'paradas':>8} {'veh':>4} | {'propio km/par':>14} {'serv':>5} {'tiempo':>9} | "
    f"{'OR-Tools km/par':>16} {'serv':>5} {'tiempo':>9} | {'brecha':>8}"
)


def tabla_referencia(titulo: str, cobertura: float, repeticiones: int, limite: float) -> None:
    print(f"\n{titulo}\n")
    print(ENCABEZADO_REF)
    print("-" * len(ENCABEZADO_REF))
    for n, vehiculos in ESCENARIOS:
        corridas = [
            correr_con_referencia(n, vehiculos, cobertura, seed, limite)
            for seed in range(repeticiones)
        ]
        med = {k: statistics.mean(c[k] for c in corridas) for k in corridas[0]}
        print(
            f"{n:>8} {vehiculos:>4} | {med['propio_km_parada']:>14.3f} "
            f"{med['propio_servidas']:>5.0f} {med['propio_ms']:>7.0f}ms | "
            f"{med['ref_km_parada']:>16.3f} {med['ref_servidas']:>5.0f} "
            f"{med['ref_ms']:>7.0f}ms | {med['brecha']:>+7.1f}%"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticiones", type=int, default=REPETICIONES)
    parser.add_argument(
        "--referencia",
        action="store_true",
        help="anade la comparacion contra OR-Tools (lenta, requiere requirements-dev)",
    )
    parser.add_argument(
        "--limite-ortools",
        type=float,
        default=LIMITE_SEGUNDOS,
        help="segundos que se le dan a OR-Tools por instancia",
    )
    args = parser.parse_args()

    print("\nmilkrun - benchmark del optimizador")
    print(f"promedio de {args.repeticiones} instancias por fila; distancias en km")

    tabla("FLOTA DIMENSIONADA (capacidad = 120% de la demanda)", 1.2, args.repeticiones)
    tabla("FLOTA SATURADA (capacidad = 80% de la demanda)", 0.8, args.repeticiones)

    print(
        "\nLa mejora se calcula sobre km por parada entregada, no sobre km totales:\n"
        "un metodo que entrega menos recorre menos, y eso no lo hace mejor.\n"
    )

    if not args.referencia:
        return

    if not disponible():
        print("--referencia necesita ortools: pip install -r requirements-dev.txt\n")
        return

    print(
        f"\n{'=' * 80}\nREFERENCIA CONTRA OR-TOOLS\n\n"
        f"OR-Tools recibe {args.limite_ortools:.0f}s por instancia; el solver propio\n"
        "corre hasta terminar. No es una comparacion de igual a igual y no\n"
        "pretende serlo: la pregunta es cuanta calidad compra ese tiempo extra.\n"
        "Brecha positiva = el solver propio recorre mas."
    )

    tabla_referencia(
        "FLOTA DIMENSIONADA (capacidad = 120% de la demanda)",
        1.2,
        args.repeticiones,
        args.limite_ortools,
    )
    tabla_referencia(
        "FLOTA SATURADA (capacidad = 80% de la demanda)",
        0.8,
        args.repeticiones,
        args.limite_ortools,
    )
    print()


if __name__ == "__main__":
    main()
