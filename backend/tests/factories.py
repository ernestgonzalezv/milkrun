"""Constructores de datos de prueba.

Separados del conftest para poder importarlos explicitamente desde cualquier
modulo de test; el conftest queda solo con fixtures.
"""

from __future__ import annotations

import random
from datetime import date

from optimizer import Fleet, Point, Stop, Vehicle

HABANA = Point(23.1136, -82.3666)
HOY = date(2026, 9, 11)


def random_stops(
    n: int,
    seed: int,
    center: Point = HABANA,
    spread: float = 0.06,
    max_demand: int = 6,
) -> tuple[Stop, ...]:
    """Paradas pseudoaleatorias reproducibles alrededor de un centro."""
    rng = random.Random(seed)
    return tuple(
        Stop(
            id=f"S{i:04d}",
            point=Point(
                center.lat + rng.uniform(-spread, spread),
                center.lon + rng.uniform(-spread * 1.5, spread * 1.5),
            ),
            demand=rng.randint(1, max_demand),
            service_minutes=rng.choice([4.0, 6.0, 8.0]),
        )
        for i in range(n)
    )


def homogeneous_fleet(count: int, capacity: float = 45.0, depot: Point = HABANA) -> Fleet:
    return Fleet(
        depot=depot,
        vehicles=tuple(
            Vehicle(id=f"V{k}", capacity=capacity, max_shift_minutes=600.0, avg_speed_kmh=25.0)
            for k in range(count)
        ),
    )


def fleet_for_demand(stops, vehicles: int = 6, slack: float = 1.2) -> Fleet:
    """Flota dimensionada para cubrir la demanda con un margen.

    Es como se arma una flota en la practica: el despachador sabe cuanto
    tiene que mover y contrata capacidad para eso, mas un colchon.
    """
    demanda = sum(s.demand for s in stops)
    return homogeneous_fleet(vehicles, capacity=demanda * slack / vehicles)
