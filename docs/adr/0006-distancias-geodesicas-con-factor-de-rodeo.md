# 0006 - Distancias haversine con factor de rodeo, no matriz por calle

Fecha: 2026-09-11
Estado: aceptada

## Contexto

Optimizar rutas requiere una matriz de distancias entre todos los puntos. Con
n paradas son n(n+1)/2 pares: para 200 paradas, 20 100 distancias.

La distancia buena es la que sigue las calles. Se obtiene de un servicio de
ruteo (OSRM, Valhalla, Google) y cuesta una peticion por matriz, o levantar y
mantener un servidor con el mapa de la ciudad.

## Decision

Distancia de circulo maximo (haversine) multiplicada por un factor de rodeo
de 1.35, que es el valor tipico reportado para malla urbana.

```
d_estimada = haversine(a, b) * 1.35
```

El factor es un parametro de `DistanceMatrix`, no una constante enterrada.

## Consecuencias

- La matriz se calcula en memoria, sin red y sin servicios externos. Para 400
  paradas son 80 200 distancias en decimas de segundo.
- Las distancias absolutas del plan son estimaciones, y el README lo dice. No
  sirven para facturarle kilometros a un cliente.
- Lo que si es solido es la comparacion: el plan, el vecino mas cercano y el
  orden de llegada se miden todos con la misma regla, asi que el porcentaje
  de mejora es valido aunque la escala tenga sesgo.
- El sesgo es sistematico, no aleatorio: penaliza por igual a todos los
  metodos, y por eso no cambia que ruta gana.
- Donde mas se nota el error es cuando hay una barrera fisica en el medio (la
  bahia de La Habana, por ejemplo): dos puntos a 2 km en linea recta pueden
  estar a 12 km por tunel. Es la limitacion conocida de este enfoque.

## Alternativas descartadas

**OSRM propio en Docker.** Es la mejora correcta y esta contemplada: solo hay
que cambiar `DistanceMatrix` por una que consulte a OSRM, sin tocar el solver.
Se descarta hoy por el costo de operar el servicio y el mapa.

**Distancia Manhattan.** Mejor en una cuadricula perfecta, peor en una ciudad
real con diagonales y calles que no cierran.

**Guardar la matriz completa en memoria como n x n.** Se guarda solo el
triangulo inferior en una lista plana: la mitad de memoria y el mismo acceso
O(1). Con 400 paradas la diferencia es 80 mil floats contra 160 mil.
