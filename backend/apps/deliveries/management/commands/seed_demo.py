"""Carga un dia de reparto de ejemplo.

    python manage.py seed_demo --stops 60 --date 2026-09-11

Las coordenadas son aproximadas pero reales: caen en calles de La Habana, no
en un cuadrado aleatorio. Importa porque un VRP sobre puntos uniformemente
distribuidos se ve bonito y no se parece en nada a una ciudad real, donde la
densidad de entregas se concentra en unos pocos corredores.
"""

from __future__ import annotations

import random
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.deliveries.models import Stop
from apps.deliveries.seed_cities import CITIES, DEFAULT_CITY, City
from apps.fleet.models import Depot, DriverProfile, Vehicle
from apps.routing.models import Route, RouteStatus
from config import container
from domain.entities import DeliveryEvent as DomainEvent
from domain.values import EventKind as DomainEventKind
from domain.values import FailureReason as DomainFailureReason

DEMO_PASSWORD = "milkrun"


class Command(BaseCommand):
    help = "Creates a depot, fleet, drivers and sample stops for one of the demo cities."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--city",
            choices=sorted(CITIES),
            default=DEFAULT_CITY,
            help="Which city to seed. Each one has its own depot, fleet and drivers.",
        )
        parser.add_argument("--stops", type=int, default=90, help="Paradas a crear.")
        parser.add_argument("--vehicles", type=int, default=6, help="Vehiculos de la flota.")
        parser.add_argument("--seed", type=int, default=2026, help="Semilla, para reproducir.")
        parser.add_argument("--date", type=str, default=None, help="Fecha YYYY-MM-DD.")
        parser.add_argument(
            "--coverage",
            type=float,
            default=1.25,
            help=(
                "Capacidad total de la flota como multiplo de la demanda del dia. "
                "1.25 es una operacion normal; por debajo de 1.0 se fuerza el caso "
                "de flota saturada, con paradas que quedan sin asignar."
            ),
        )
        parser.add_argument(
            "--progress",
            type=float,
            default=0.0,
            help="Fraccion del dia ya trabajada (0 a 1). Requiere un plan ya creado.",
        )
        parser.add_argument(
            "--plan", action="store_true", help="Planificar el dia despues de crear los datos."
        )
        parser.add_argument(
            "--reset", action="store_true", help="Borra las paradas de esa fecha antes de crear."
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        city = CITIES[options["city"]]
        rng = random.Random(options["seed"])
        dia = (
            timezone.datetime.strptime(options["date"], "%Y-%m-%d").date()
            if options["date"]
            else timezone.localdate()
        )

        depot = self._depot(city)

        if options["reset"]:
            Route.objects.filter(depot=depot, date=dia).delete()
            borradas, _ = Stop.objects.filter(depot=depot, scheduled_date=dia).delete()
            self.stdout.write(f"  borradas {borradas} filas de la fecha {dia}")

        paradas = self._stops(depot, city, dia, options["stops"], rng)

        demanda = sum(p.demand for p in paradas)
        vehiculos = self._vehicles(depot, city, options["vehicles"], demanda, options["coverage"])
        self._dispatcher()
        self._drivers(depot, city, vehiculos)

        plan = None
        if options["plan"] or options["progress"] > 0:
            plan = container.plan_day()(depot.id, dia, replan=True)
        if options["progress"] > 0:
            if plan is None:
                raise CommandError("--progress necesita un plan; usa tambien --plan.")
            self._simular_avance(plan, options["progress"], rng)

        capacidad = sum(v.capacity for v in vehiculos)
        demanda_total = sum(p.demand for p in paradas)

        self.stdout.write(self.style.SUCCESS(f"\n  {city.label}, {depot.name}"))
        self.stdout.write(f"  {depot.address}")
        self.stdout.write(
            f"  Fleet: {len(vehiculos)} vehicles "
            f"(capacity {capacidad:.0f} against demand of {demanda_total:.0f})"
        )
        self.stdout.write(f"  Stops: {len(paradas)} for {dia:%d/%m/%Y}")
        if plan is not None:
            metricas = plan.metrics
            self.stdout.write(
                f"  Plan: {len(plan.routes)} routes, {metricas['stops_served']} stops, "
                f"{metricas['total_km']:.1f} km, "
                f"{metricas['improvement_vs_nearest_neighbor_pct']:.1f}% better than manual routing"
            )
            if plan.unassigned:
                self.stdout.write(self.style.WARNING(f"  Unassigned: {len(plan.unassigned)} stops"))
        self.stdout.write(
            f"\n  Dispatcher:  dispatch / {DEMO_PASSWORD}"
            f"\n  Driver:      driver-{city.key}-1 / {DEMO_PASSWORD}"
            f"\n\n  Plan it:  POST /api/v1/routes/plan/ "
            f'{{"depot": {depot.id}, "date": "{dia}"}}\n'
        )

    def _simular_avance(self, plan, fraccion: float, rng: random.Random) -> None:
        """Marca como trabajadas las primeras paradas de cada ruta.

        Se escriben eventos reales y se recalcula el estado con la misma
        funcion que usa la API, en vez de tocar `Stop.status` a mano: si la
        proyeccion tuviera un bug, la demo lo mostraria igual que produccion.
        """
        ahora = timezone.now()
        creados = 0
        eventos = container.sync_driver_events()
        for ruta in plan.routes:
            if ruta.driver_id is None:
                continue
            paradas = list(ruta.stops)
            cuantas = int(len(paradas) * min(max(fraccion, 0.0), 1.0))
            for indice, route_stop in enumerate(paradas[:cuantas]):
                fallo = rng.random() < 0.125
                eventos(
                    ruta.driver_id,
                    [
                        DomainEvent(
                            id=None,
                            stop_id=route_stop.stop_id,
                            driver_id=ruta.driver_id,
                            client_event_id=uuid.uuid4(),
                            kind=DomainEventKind.FAILED if fallo else DomainEventKind.DELIVERED,
                            occurred_at=ahora - timedelta(minutes=(cuantas - indice) * 11),
                            reason=rng.choice(list(DomainFailureReason)) if fallo else None,
                            note="Nadie abrio la puerta" if fallo else "",
                        )
                    ],
                )
                creados += 1
        Route.objects.filter(date=plan.routes[0].date).update(status=RouteStatus.IN_PROGRESS)
        self.stdout.write(f"  Avance simulado: {creados} paradas ya trabajadas")

    def _depot(self, city: City) -> Depot:
        depot, _ = Depot.objects.get_or_create(
            name=city.depot_name,
            defaults={
                "address": city.depot_address,
                "latitude": city.depot_lat,
                "longitude": city.depot_lon,
            },
        )
        return depot

    def _vehicles(
        self, depot: Depot, city: City, cantidad: int, demanda: float, cobertura: float
    ) -> list[Vehicle]:
        """Flota mixta: dos motos chicas y el resto camionetas.

        Las capacidades se reparten de forma que el total sea `cobertura` veces
        la demanda. Una moto lleva un tercio de lo que lleva una camioneta.
        """
        pesos = [1.0 if k < 2 else 3.0 for k in range(cantidad)]
        unidad = demanda * cobertura / sum(pesos)

        vehiculos = []
        for k, peso in enumerate(pesos):
            es_moto = peso == 1.0
            codigo = f"{city.code}-{'MOT' if es_moto else 'VAN'}-{k + 1:02d}"
            vehiculo, creado = Vehicle.objects.get_or_create(
                code=codigo,
                defaults={
                    "depot": depot,
                    "plate": rng_plate(city.code, k),
                    "capacity": round(unidad * peso, 1),
                    "max_shift_minutes": 420 if es_moto else 480,
                    "avg_speed_kmh": 28.0 if es_moto else 22.0,
                },
            )
            if not creado:
                vehiculo.capacity = round(unidad * peso, 1)
                vehiculo.save(update_fields=["capacity"])
            vehiculos.append(vehiculo)
        return vehiculos

    def _dispatcher(self) -> User:
        user, creado = User.objects.get_or_create(
            username="dispatch",
            defaults={
                "first_name": "Marta",
                "last_name": "Cabrera",
                "role": Role.DISPATCHER,
                "is_staff": True,
                "is_superuser": True,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        if creado:
            self.stdout.write("  creado usuario despachador")
        return user

    def _drivers(self, depot: Depot, city: City, vehiculos: list[Vehicle]) -> list[DriverProfile]:
        perfiles = []
        for k, vehiculo in enumerate(vehiculos, start=1):
            nombre = city.names[k % len(city.names)]
            user, _ = User.objects.get_or_create(
                username=f"driver-{city.key}-{k}",
                defaults={
                    "first_name": nombre.split()[0],
                    "last_name": nombre.split()[-1],
                    "role": Role.DRIVER,
                    "password": make_password(DEMO_PASSWORD),
                },
            )
            perfil, _ = DriverProfile.objects.get_or_create(
                user=user, defaults={"depot": depot, "default_vehicle": vehiculo}
            )
            perfiles.append(perfil)
        return perfiles

    def _stops(
        self, depot: Depot, city: City, dia, cantidad: int, rng: random.Random
    ) -> list[Stop]:
        paradas = []
        for _ in range(cantidad):
            zona = rng.choice(city.zones)
            paradas.append(
                Stop(
                    depot=depot,
                    customer_name=rng.choice(city.names),
                    phone=f"{city.phone_prefix} {rng.randint(200, 989)}-{rng.randint(1000, 9999)}",
                    address=city.address(rng.randint(2, 980), zona),
                    latitude=zona.latitude + rng.uniform(-0.003, 0.003),
                    longitude=zona.longitude + rng.uniform(-0.003, 0.003),
                    demand=round(rng.uniform(0.5, 5.0), 1),
                    service_minutes=rng.choice([3, 5, 5, 8, 12]),
                    scheduled_date=dia + timedelta(days=0),
                    notes=rng.choice(city.notes),
                )
            )
        return Stop.objects.bulk_create(paradas)


def rng_plate(city_code: str, k: int) -> str:
    """Deterministic plate. The city code goes in because plates repeated
    across cities when the only input was the index."""
    letras = f"{chr(65 + k % 26)}{chr(65 + (k * 3) % 26)}"
    return f"{city_code}-{letras}{100 + k * 7:03d}"
