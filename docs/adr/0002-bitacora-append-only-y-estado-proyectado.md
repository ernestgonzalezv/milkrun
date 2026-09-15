# 0002 - El estado de una entrega es una proyeccion, no un campo editable

Fecha: 2026-09-11
Estado: aceptada

## Contexto

Una parada pasa por varios estados: pendiente, planificada, en camino,
entregada o fallida. El modelo obvio es un campo `status` que se actualiza.

El problema aparece con la app movil. El chofer trabaja sin senal buena: los
eventos se encolan en el telefono y se envian cuando hay cobertura. Eso
significa que llegan **tarde, repetidos y desordenados**. Con un `status`
mutable, un evento viejo que llega tarde pisa uno nuevo y la parada aparece
"en camino" despues de haber sido entregada.

## Decision

Los hechos se guardan en `DeliveryEvent`, una tabla append-only. `Stop.status`
es una proyeccion de esa bitacora, recalculada desde cero cada vez que entra
un evento, tomando el ultimo por `occurred_at` (hora del dispositivo).

`Stop.status` es `editable=False` y el admin no permite crear ni modificar
eventos.

## Consecuencias

- El orden de llegada deja de importar. Solo importa cuando ocurrio el hecho.
- Se puede reconstruir que sabia el sistema en cualquier momento del pasado.
  Para un reclamo de un cliente eso es la diferencia entre tener prueba y no
  tenerla.
- Un bug en la regla de proyeccion se arregla y se recalcula. Los hechos no
  se pierden nunca, que es la propiedad que justifica todo lo demas.
- Cuesta una consulta extra por evento recibido. Con el indice
  `event_stop_time_idx` es irrelevante frente al volumen real.
- La cancelacion es la excepcion: es una decision de oficina y el terreno no
  la revierte. Esta explicito en `services.project_status`.

## Alternativas descartadas

**Campo mutable con validacion de transiciones.** Mas simple, pero no
resuelve el desorden: para decidir si una transicion es valida hay que saber
que paso antes, y eso es tener la bitacora igual, solo que a medias.

**Event sourcing completo** (tambien para paradas, rutas y flota). Exagerado.
El desorden temporal solo ocurre en lo que reporta el movil; el catalogo lo
edita una persona sentada frente a una pantalla con conexion.
