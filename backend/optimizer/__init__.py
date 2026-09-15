"""Motor de optimizacion de rutas (VRP con capacidad y jornada maxima).

Paquete deliberadamente puro: no importa Django ni toca base de datos.
Se puede usar, testear y perfilar de forma aislada.
"""

from .models import Fleet, Plan, Point, Route, Stop, Vehicle
from .solver import solve

__all__ = ["Fleet", "Plan", "Point", "Route", "Stop", "Vehicle", "solve"]
