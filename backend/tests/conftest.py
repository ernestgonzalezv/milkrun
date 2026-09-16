"""Fixtures compartidas."""

from __future__ import annotations

import pytest

from optimizer import Fleet, Stop

from .factories import homogeneous_fleet, random_stops


@pytest.fixture
def small_instance() -> tuple[Fleet, tuple[Stop, ...]]:
    return homogeneous_fleet(3), random_stops(25, seed=7)


@pytest.fixture
def large_instance() -> tuple[Fleet, tuple[Stop, ...]]:
    return homogeneous_fleet(8, capacity=60.0), random_stops(120, seed=99)


@pytest.fixture(autouse=True)
def throttle_limpio():
    """Aisla el rate limiting entre tests.

    DRF cuenta las peticiones en la cache, que vive en el proceso y sobrevive
    de un test al siguiente. Sin esto, el test numero 21 falla con 429 por
    culpa de los veinte anteriores. Se limpia en vez de desactivar el
    throttling, para que siga siendo codigo ejercitado.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def depot(db):
    from apps.fleet.models import Depot

    return Depot.objects.create(
        name="Almacen Boyeros", address="Rancho Boyeros", latitude=23.0553, longitude=-82.3822
    )


@pytest.fixture
def vehicles(depot):
    from apps.fleet.models import Vehicle

    return [
        Vehicle.objects.create(
            depot=depot,
            code=f"CAM-{k:02d}",
            capacity=60.0,
            max_shift_minutes=480,
            avg_speed_kmh=25.0,
        )
        for k in range(1, 4)
    ]


@pytest.fixture
def dispatcher(db):
    from apps.accounts.models import Role, User

    return User.objects.create_user(
        username="marta", password="clave-de-prueba", role=Role.DISPATCHER
    )


@pytest.fixture
def drivers(depot, vehicles):
    from apps.accounts.models import Role, User
    from apps.fleet.models import DriverProfile

    perfiles = []
    for k, vehiculo in enumerate(vehicles, start=1):
        user = User.objects.create_user(
            username=f"chofer{k}",
            password="clave-de-prueba",
            first_name=f"Chofer{k}",
            last_name="Prueba",
            role=Role.DRIVER,
        )
        perfiles.append(
            DriverProfile.objects.create(user=user, depot=depot, default_vehicle=vehiculo)
        )
    return perfiles


@pytest.fixture
def stops_hoy(depot):
    """Paradas dispersas en La Habana para una fecha fija."""
    import random as _random

    from apps.deliveries.models import Stop

    from .factories import HOY

    rng = _random.Random(5)
    return [
        Stop.objects.create(
            depot=depot,
            customer_name=f"Cliente {i} Apellido",
            phone=f"+53 5{1000000 + i}",
            address=f"Calle {i} No. {i * 3}, La Habana",
            latitude=23.1136 + rng.uniform(-0.05, 0.05),
            longitude=-82.3666 + rng.uniform(-0.07, 0.07),
            demand=rng.uniform(1.0, 4.0),
            service_minutes=5,
            scheduled_date=HOY,
        )
        for i in range(30)
    ]


@pytest.fixture
def api():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def as_dispatcher(api, dispatcher):
    api.force_authenticate(dispatcher)
    return api


@pytest.fixture
def as_driver(api, drivers):
    api.force_authenticate(drivers[0].user)
    return api


@pytest.fixture
def ruta_con_parada(depot, vehicles, drivers):
    """Deja una parada asignada al primer chofer.

    El caso de uso de sincronizacion rechaza hechos sobre paradas que no son
    del chofer, asi que los tests que reportan desde terreno necesitan que la
    parada este en una ruta suya.
    """
    from apps.routing.models import Route, RouteStop

    def _assign(stop):
        route = Route.objects.create(
            depot=depot, vehicle=vehicles[0], driver=drivers[0].user, date=stop.scheduled_date
        )
        RouteStop.objects.create(route=route, stop=stop, sequence=1)
        return route

    return _assign
