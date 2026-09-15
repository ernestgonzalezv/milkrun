# 0001 - Resolver el VRP con una heuristica propia, no con OR-Tools ni una API

Fecha: 2026-09-11
Estado: aceptada

## Contexto

El nucleo del producto es decidir que paradas van en que camion y en que
orden. Es un VRP con capacidad y jornada maxima: NP-duro, sin solucion exacta
practica por encima de ~50 paradas.

Habia tres caminos:

1. Llamar a una API de ruteo (Google Routes, Mapbox Optimization, HERE).
2. Usar OR-Tools de Google, que trae un solver de VRP muy bueno.
3. Implementar Clarke-Wright + busqueda local a mano.

## Decision

Se implementa a mano: ahorros de Clarke-Wright para construir, 2-opt y Or-opt
para mejorar, e insercion mas barata para cubrir lo que quedo suelto.

Las tres razones, en orden de peso real:

- **Costo y dependencia.** Las APIs cobran por peticion y exigen tarjeta y
  conectividad estable. Para un despacho que replanifica varias veces al dia
  desde Cuba eso es un problema operativo, no solo de precio.
- **Control del modelo.** La jornada maxima, el tiempo de servicio por parada
  y la flota mixta son restricciones del negocio. Con un solver propio se
  ajustan en el codigo; con una API se pelea contra su modelo de datos.
- **Se puede explicar.** Cada decision del plan es rastreable hasta una
  formula de ocho lineas. Cuando el despachador pregunta "por que este camion
  fue hasta Guanabacoa", hay respuesta.

## Consecuencias

- El plan no es optimo. Clarke-Wright con 2-opt queda tipicamente entre 5% y
  10% por encima del optimo practico; a cambio resuelve 400 paradas en menos
  de medio segundo.
- Hay que sostener la calidad con tests y benchmark propios, porque no hay un
  proveedor que responda por el resultado. Ver `optimizer/benchmark.py`.
- Las distancias son geodesicas con factor de rodeo, no distancias por calle.
  Ver ADR 0006.

## Alternativas descartadas

**OR-Tools.** Es mejor solver que este, sin discusion. Se descarto por peso
(la rueda pasa de 40 MB) y porque su API de restricciones es un lenguaje
propio: la curva de aprendizaje es mas larga que escribir la heuristica, y el
plan resultante es mas dificil de justificar ante un usuario. Sigue siendo la
mejora natural si el volumen crece; el paquete `optimizer` esta aislado
justamente para poder cambiarlo sin tocar el resto.

**API de ruteo.** Descartada por costo por peticion y por dependencia de
conectividad en el momento de planificar.
