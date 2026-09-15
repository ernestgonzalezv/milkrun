# Imagen del backend. Multi-stage para que la capa final no cargue con las
# herramientas de compilacion de las dependencias.
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.txt


FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Usuario sin privilegios: si alguien escapa del proceso, no cae en root.
RUN useradd --create-home --uid 1000 milkrun

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=milkrun:milkrun . .

USER milkrun
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/schema/')"

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--access-logfile", "-"]
