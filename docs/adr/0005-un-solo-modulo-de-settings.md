# 0005 - Un unico settings.py parametrizado por entorno

Fecha: 2026-09-11
Estado: aceptada

## Contexto

La convencion extendida es partir la configuracion en
`settings/base.py`, `settings/dev.py`, `settings/prod.py`.

## Decision

Un solo `config/settings.py` que lee variables de entorno, con `.env` para
desarrollo y `.env.example` versionado.

## Consecuencias

- Se elimina la clase de bug mas cara de esa convencion: arrancar produccion
  con el settings equivocado. No hay settings equivocado que elegir.
- La diferencia entre entornos queda visible en un solo archivo, en vez de
  repartida en una jerarquia de imports.
- `DJANGO_SECRET_KEY` ausente con `DEBUG=0` levanta `RuntimeError` al
  arrancar, no un fallo silencioso con una clave por defecto.
- Las banderas de seguridad (HSTS, cookies seguras, redireccion a HTTPS) se
  activan solas cuando `DEBUG=0`, sin que nadie tenga que acordarse.
- Si el proyecto creciera a muchos entornos con diferencias estructurales,
  esta decision habria que revisarla. Con dos entornos y seis variables, no.

## Alternativas descartadas

**Paquete `settings/` por entorno.** Mas ceremonia de la que este proyecto
justifica hoy.

**django-environ / django-configurations.** Una dependencia mas para lo que
resuelven veinte lineas de `os.getenv` con dos ayudantes de parseo.
