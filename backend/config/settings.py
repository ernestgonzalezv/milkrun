"""Configuracion de Django para milkrun.

Un solo modulo de settings parametrizado por entorno, no un paquete
`settings/base|dev|prod`: con seis variables de entorno no hace falta la
ceremonia, y evita el clasico "en prod se importo el settings equivocado".
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(int(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = env_flag("DJANGO_DEBUG", default=True)

# En desarrollo hay una clave por defecto para que `runserver` arranque sin
# configurar nada; en produccion la ausencia de la variable es un error duro.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("DJANGO_SECRET_KEY es obligatoria cuando DEBUG=0")
    SECRET_KEY = "clave-insegura-solo-para-desarrollo"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,10.0.2.2,testserver")

# En ECS Fargate la sonda del balanceador no llega con el nombre de dominio:
# llega con Host = IP privada de la tarea, que no existe hasta que la tarea
# arranca y por tanto no se puede poner en DJANGO_ALLOWED_HOSTS desde Terraform.
# Sin esto, Django responde 400 a cada health check, el ALB da la tarea por no
# sana, ECS la mata, y el servicio no llega a estabilizarse nunca.
#
# ECS publica esa IP en un endpoint de metadatos interno. La variable solo
# existe dentro de ECS, asi que en local y en los tests esto no hace nada.
if _metadata_uri := os.getenv("ECS_CONTAINER_METADATA_URI_V4"):
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(_metadata_uri, timeout=1) as _respuesta:
            _meta = json.load(_respuesta)
        ALLOWED_HOSTS += [
            _ip for _red in _meta.get("Networks", []) for _ip in _red.get("IPv4Addresses", [])
        ]
    except Exception:
        # Arrancar sin la IP es preferible a no arrancar: si el ALB rechaza la
        # tarea se vera en el health check, y el fallo queda acotado a una tarea.
        pass

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "apps.accounts",
    "apps.fleet",
    "apps.deliveries",
    "apps.routing",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Havana"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {"tracking": "60/min", "planning": "20/min"},
    # Traduce los errores de dominio a codigos HTTP en un solo sitio, para que
    # ninguna vista tenga que envolver el caso de uso en un try.
    "EXCEPTION_HANDLER": "apps.shared.http.domain_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),  # cubre una jornada de reparto
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "milkrun API",
    "DESCRIPTION": "Delivery route planning and live tracking.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # The groups are ordered by the arc of a working day rather than
    # alphabetically: sign in, plan, deliver, track. Whoever opens this for the
    # first time reads it top to bottom.
    "SORT_OPERATIONS": False,
    "TAGS": [
        {
            "name": "Authentication",
            "description": "JWT tokens and the signed-in user. Everything else requires them.",
        },
        {
            "name": "Planning",
            "description": (
                "The core. `routes/plan/` runs the VRP solver and persists the day's plan; "
                "the rest reads back what it produced."
            ),
        },
        {
            "name": "Deliveries",
            "description": "Creating and reading stops: the orders to be delivered.",
        },
        {
            "name": "Driver app",
            "description": (
                "What the Android app consumes, including the offline queue sync. That sync "
                "is idempotent: resending the same batch duplicates nothing."
            ),
        },
        {
            "name": "Public tracking",
            "description": (
                "No authentication. This is the link the end customer receives, rate limited "
                "per IP and with personal data trimmed."
            ),
        },
        {
            "name": "Fleet",
            "description": "Reference catalogues: depots, vehicles and drivers.",
        },
    ],
    # Tres modelos distintos tienen un campo `status`; sin estos alias el
    # generador inventa nombres como `Status6b4Enum` y el cliente TypeScript
    # queda ilegible.
    "ENUM_NAME_OVERRIDES": {
        "StopStatusEnum": "apps.deliveries.models.StopStatus.choices",
        "RouteStatusEnum": "apps.routing.models.RouteStatus.choices",
        "EventKindEnum": "apps.deliveries.models.EventKind.choices",
        "FailureReasonEnum": "apps.deliveries.models.FailureReason.choices",
    },
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"apps": {"level": "DEBUG" if DEBUG else "INFO"}},
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Sin esta exencion, SECURE_SSL_REDIRECT contesta 301 a la sonda del ALB,
    # que llega por HTTP desde dentro de la VPC. El ALB lo lee como no sana,
    # mata la tarea, arranca otra, y el ciclo no termina nunca.
    SECURE_REDIRECT_EXEMPT = [r"^healthz$", r"^readyz$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
