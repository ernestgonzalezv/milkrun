"""Real cities the demo can be seeded with.

Coordinates are block-level approximations of actual neighbourhoods, not random
points in a bounding box. It matters more than it looks: a VRP over uniformly
scattered points produces pretty routes that say nothing, because real delivery
demand concentrates along a handful of corridors and the whole difficulty of the
problem comes from that clustering.

Depots sit where freight actually stages in each city — Maspeth for New York,
Pilsen for Chicago, Vernon for Los Angeles — so the first and last leg of every
route have realistic length.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Zone:
    neighbourhood: str
    street: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class City:
    key: str
    code: str
    label: str
    depot_name: str
    depot_address: str
    depot_lat: float
    depot_lon: float
    region: str
    phone_prefix: str
    zones: tuple[Zone, ...]
    names: tuple[str, ...]
    notes: tuple[str, ...]

    def address(self, number: int, zone: Zone) -> str:
        return f"{number} {zone.street}, {zone.neighbourhood}, {self.region}"


_US_NOTES = (
    "", "", "",
    "Ring the buzzer for 2F",
    "Leave with the doorman if nobody answers",
    "Call on arrival",
    "Walk-up, no elevator",
    "Side entrance off the alley",
    "Gate code at the callbox",
)

NEW_YORK = City(
    key="nyc",
    code="NYC",
    label="New York City",
    depot_name="Maspeth Distribution Center",
    depot_address="58-49 Grand Ave, Maspeth, Queens, NY",
    depot_lat=40.7220,
    depot_lon=-73.9090,
    region="NY",
    phone_prefix="+1 (212)",
    zones=(
        Zone("Financial District", "Wall St", 40.7069, -74.0113),
        Zone("Tribeca", "Hudson St", 40.7195, -74.0089),
        Zone("SoHo", "Broadway", 40.7233, -74.0030),
        Zone("East Village", "Avenue A", 40.7265, -73.9815),
        Zone("Chelsea", "W 23rd St", 40.7456, -74.0000),
        Zone("Midtown", "W 42nd St", 40.7570, -73.9877),
        Zone("Upper West Side", "Columbus Ave", 40.7870, -73.9754),
        Zone("Upper East Side", "Lexington Ave", 40.7736, -73.9600),
        Zone("Harlem", "W 125th St", 40.8100, -73.9465),
        Zone("Washington Heights", "Broadway", 40.8500, -73.9370),
        Zone("Williamsburg", "Bedford Ave", 40.7170, -73.9570),
        Zone("Bushwick", "Knickerbocker Ave", 40.7000, -73.9200),
        Zone("Park Slope", "5th Ave", 40.6720, -73.9830),
        Zone("Bedford-Stuyvesant", "Nostrand Ave", 40.6870, -73.9500),
        Zone("Downtown Brooklyn", "Fulton St", 40.6900, -73.9840),
        Zone("Astoria", "Steinway St", 40.7650, -73.9200),
        Zone("Long Island City", "Jackson Ave", 40.7470, -73.9430),
        Zone("Flushing", "Main St", 40.7590, -73.8300),
        Zone("Jackson Heights", "Roosevelt Ave", 40.7470, -73.8890),
        Zone("Sunnyside", "Queens Blvd", 40.7430, -73.9200),
        Zone("South Bronx", "E 149th St", 40.8160, -73.9200),
        Zone("Fordham", "E Fordham Rd", 40.8620, -73.8900),
    ),
    names=(
        "James Okafor", "Maria Delgado", "Aisha Rahman", "Daniel Kowalski",
        "Priya Venkatesan", "Marcus Bell", "Sofia Restrepo", "Kevin Nguyen",
        "Rachel Feldman", "Omar Haddad", "Grace Kim", "Tyler Brennan",
        "Ana Lucia Sousa", "Dmitri Volkov", "Nia Thompson", "Carlos Mejia",
    ),
    notes=_US_NOTES,
)

CHICAGO = City(
    key="chicago",
    code="CHI",
    label="Chicago",
    depot_name="Pilsen Freight Terminal",
    depot_address="2100 S Racine Ave, Pilsen, Chicago, IL",
    depot_lat=41.8530,
    depot_lon=-87.6560,
    region="IL",
    phone_prefix="+1 (312)",
    zones=(
        Zone("The Loop", "S State St", 41.8830, -87.6280),
        Zone("River North", "N Clark St", 41.8930, -87.6310),
        Zone("West Loop", "W Randolph St", 41.8840, -87.6480),
        Zone("Wicker Park", "N Milwaukee Ave", 41.9080, -87.6770),
        Zone("Logan Square", "N Kedzie Ave", 41.9290, -87.7070),
        Zone("Lincoln Park", "N Halsted St", 41.9210, -87.6490),
        Zone("Lakeview", "N Broadway", 41.9400, -87.6440),
        Zone("Uptown", "N Sheridan Rd", 41.9660, -87.6550),
        Zone("Rogers Park", "N Clark St", 42.0100, -87.6700),
        Zone("Hyde Park", "E 53rd St", 41.7990, -87.5900),
        Zone("Bronzeville", "S King Dr", 41.8200, -87.6160),
        Zone("Pilsen", "W 18th St", 41.8570, -87.6560),
        Zone("Little Village", "W 26th St", 41.8440, -87.7020),
        Zone("Bridgeport", "S Halsted St", 41.8380, -87.6470),
        Zone("Humboldt Park", "N California Ave", 41.9010, -87.6970),
        Zone("Albany Park", "W Lawrence Ave", 41.9680, -87.7160),
        Zone("Avondale", "N Belmont Ave", 41.9390, -87.7110),
        Zone("Garfield Park", "W Madison St", 41.8810, -87.7170),
    ),
    names=(
        "Brian Sullivan", "Latoya Jackson", "Michael Ortiz", "Hannah Weiss",
        "Andre Wilkins", "Elena Petrova", "Jorge Villanueva", "Claire Donnelly",
        "Samuel Adeyemi", "Megan Foster", "Raj Patel", "Denise Carter",
        "Anthony Russo", "Fatima Zahra", "Peter Lindqvist", "Yolanda Rios",
    ),
    notes=_US_NOTES,
)

LOS_ANGELES = City(
    key="la",
    code="LAX",
    label="Los Angeles",
    depot_name="Vernon Logistics Hub",
    depot_address="3200 E Vernon Ave, Vernon, CA",
    depot_lat=34.0030,
    depot_lon=-118.2300,
    region="CA",
    phone_prefix="+1 (213)",
    zones=(
        Zone("Downtown", "S Broadway", 34.0450, -118.2510),
        Zone("Koreatown", "Wilshire Blvd", 34.0580, -118.3010),
        Zone("Hollywood", "Sunset Blvd", 34.0980, -118.3260),
        Zone("Silver Lake", "Sunset Blvd", 34.0830, -118.2700),
        Zone("Echo Park", "Glendale Blvd", 34.0780, -118.2600),
        Zone("Los Feliz", "Hillhurst Ave", 34.1060, -118.2870),
        Zone("Westwood", "Westwood Blvd", 34.0630, -118.4450),
        Zone("Santa Monica", "Wilshire Blvd", 34.0250, -118.4960),
        Zone("Venice", "Abbot Kinney Blvd", 33.9910, -118.4650),
        Zone("Culver City", "Washington Blvd", 34.0210, -118.3960),
        Zone("Inglewood", "Market St", 33.9610, -118.3530),
        Zone("Boyle Heights", "Cesar E Chavez Ave", 34.0450, -118.2050),
        Zone("East Los Angeles", "Whittier Blvd", 34.0230, -118.1720),
        Zone("Highland Park", "N Figueroa St", 34.1120, -118.1920),
        Zone("Glendale", "N Brand Blvd", 34.1480, -118.2550),
        Zone("Pasadena", "E Colorado Blvd", 34.1460, -118.1350),
        Zone("Long Beach", "Pine Ave", 33.7700, -118.1930),
        Zone("Torrance", "Hawthorne Blvd", 33.8350, -118.3530),
    ),
    names=(
        "Jessica Alvarez", "Devon Brooks", "Mei-Ling Chen", "Ricardo Fuentes",
        "Amber Whitfield", "Hassan Karimi", "Natalie Vargas", "Christopher Doyle",
        "Imani Robinson", "Luis Beltran", "Sarah Kaplan", "Jae-Won Park",
        "Gabriela Nunez", "Trevor Nakamura", "Danielle Moss", "Esteban Cordero",
    ),
    notes=_US_NOTES,
)

HAVANA = City(
    key="havana",
    code="HAV",
    label="La Habana",
    depot_name="Almacen Central Habana",
    depot_address="Ave. Rancho Boyeros y Calzada de Bejucal, Boyeros",
    depot_lat=23.0553,
    depot_lon=-82.3822,
    region="La Habana",
    phone_prefix="+53 5",
    zones=(
        Zone("Habana Vieja", "Obispo", 23.1362, -82.3520),
        Zone("Habana Vieja", "Mercaderes", 23.1385, -82.3535),
        Zone("Centro Habana", "Neptuno", 23.1391, -82.3652),
        Zone("Centro Habana", "Galiano", 23.1367, -82.3639),
        Zone("Centro Habana", "Reina", 23.1305, -82.3667),
        Zone("Vedado", "Linea", 23.1418, -82.3888),
        Zone("Vedado", "Calle 23", 23.1372, -82.3861),
        Zone("Vedado", "Paseo", 23.1349, -82.3925),
        Zone("Vedado", "Calle G", 23.1385, -82.3830),
        Zone("Plaza", "Ayestaran", 23.1265, -82.3803),
        Zone("Plaza", "Boyeros", 23.1188, -82.3853),
        Zone("Cerro", "Calzada del Cerro", 23.1180, -82.3690),
        Zone("Cerro", "Infanta", 23.1272, -82.3737),
        Zone("Diez de Octubre", "Calzada de Luyano", 23.1073, -82.3437),
        Zone("Diez de Octubre", "Santos Suarez", 23.1010, -82.3618),
        Zone("Playa", "Calle 41", 23.1046, -82.4258),
        Zone("Playa", "Quinta Avenida", 23.1178, -82.4162),
        Zone("Playa", "Calle 70", 23.1105, -82.4370),
        Zone("Marianao", "Avenida 51", 23.0906, -82.4315),
        Zone("Marianao", "Calle 100", 23.0790, -82.4147),
        Zone("Boyeros", "Rancho Boyeros", 23.0472, -82.3906),
        Zone("San Miguel del Padron", "Calzada de Guines", 23.0842, -82.3163),
        Zone("Regla", "Marti", 23.1244, -82.3327),
        Zone("Guanabacoa", "Pepe Antonio", 23.1235, -82.3010),
    ),
    names=(
        "Yanet Perez", "Osmany Rodriguez", "Dayana Alvarez", "Reinier Castillo",
        "Marlen Gonzalez", "Yoandry Suarez", "Liudmila Torres", "Alexei Ramirez",
        "Damaris Fuentes", "Yusniel Blanco", "Odalys Herrera", "Maikel Cruz",
        "Yaima Delgado", "Ernesto Bermudez", "Niurka Sanchez", "Lazaro Quintana",
    ),
    notes=(
        "", "", "",
        "Ring the second floor buzzer",
        "Leave with the neighbourhood watch if nobody is in",
        "Call before arriving",
        "Building has no lift",
        "Entrance through the side passage",
    ),
)

CITIES: dict[str, City] = {c.key: c for c in (NEW_YORK, CHICAGO, LOS_ANGELES, HAVANA)}

DEFAULT_CITY = "nyc"
