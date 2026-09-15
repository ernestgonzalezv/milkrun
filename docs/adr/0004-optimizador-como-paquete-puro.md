# 0004 - El optimizador no sabe que existe Django

Fecha: 2026-09-11
Estado: aceptada

## Contexto

Lo natural en Django es poner la logica en el modelo o en el servicio de la
app. Con el optimizador eso significaria que resolver una ruta necesita una
base de datos, migraciones aplicadas y un `settings` cargado.

## Decision

`optimizer/` es un paquete de Python sin dependencias: ni Django, ni numpy,
ni nada. Habla en sus propios tipos (`Stop`, `Vehicle`, `Fleet`, `Plan`), todos
inmutables.

La traduccion entre modelos de Django y tipos del optimizador ocurre en un
unico lugar: `apps/routing/services.py`. Es la unica frontera donde los dos
mundos se cruzan.

## Consecuencias

- Los tests del solver corren en milisegundos, sin base de datos. Son 56 y
  tardan menos que un solo test de API.
- El benchmark (`python -m optimizer.benchmark`) se ejecuta sin levantar nada.
- Se puede perfilar, portar a otro proyecto o exponer como servicio aparte sin
  arrastrar el framework.
- Cambiar la heuristica (por ejemplo a OR-Tools, ver ADR 0001) toca un
  paquete y ningun modelo.
- Cuesta una capa de traduccion de unas 30 lineas. Es el precio, y es barato.

## Alternativas descartadas

**Metodos en el modelo `Route`.** Acopla el algoritmo al ORM y obliga a que
todo test de ruteo sea un test de base de datos.

**Tarea de Celery que lee y escribe directo.** Mezcla tres responsabilidades
(orquestacion, algoritmo y persistencia) en una funcion. Cuando el plan sale
mal no se sabe cual de las tres fallo.
