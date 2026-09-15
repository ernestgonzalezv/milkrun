# 0007 - Clean Architecture en el backend, con una excepción declarada

Fecha: 2026-09-13
Estado: aceptada

## Contexto

El proyecto empezó con la organización habitual de Django: modelos, servicios y
vistas por app. Funcionaba, pero tenía la flecha de dependencias al revés: las
entidades del negocio *eran* los modelos del ORM, los servicios importaban
`django.db.transaction`, y las vistas consultaban el ORM directamente.

Eso tiene tres costos concretos, no teóricos:

1. Cualquier test de una regla de negocio necesitaba migraciones aplicadas.
2. La forma de la API estaba atada a la forma del esquema.
3. Cambiar el optimizador —que el ADR 0001 promete que se puede— implicaba
   tocar el servicio que también hablaba con la base.

## Decisión

```
domain/          entidades, objetos de valor, reglas, puertos y casos de uso.
                 No importa Django. Verificado por tests/test_architecture.py.
infrastructure/  adaptadores: repositorios sobre el ORM, el planificador que
                 envuelve `optimizer/`, el reloj.
apps/            capa de entrega: modelos de persistencia, serializers y vistas.
config/container.py   raíz de composición: el único sitio que decide qué
                 adaptador concreto satisface cada puerto.
```

- Las entidades son dataclasses inmutables. Los modelos de Django quedan como
  lo que son: el esquema de persistencia.
- Los puertos son `Protocol`, no clases base. Los adaptadores no heredan nada,
  solo cumplen la forma, así el dominio no aparece en sus firmas.
- Los casos de uso reciben puertos en el constructor y exponen un único
  `__call__`. Ninguno llama a otro.
- Las vistas hacen tres cosas: validar, invocar un caso de uso y serializar.
- Los errores de dominio son excepciones del negocio; un `EXCEPTION_HANDLER`
  los traduce a códigos HTTP en un solo lugar. El caso de uso no sabe que
  existe un 409.

## La excepción: los catálogos de flota

`DepotViewSet`, `VehicleViewSet` y `DriverProfileViewSet` siguen siendo
`ModelViewSet` sobre el ORM. Es deliberado.

Son CRUD sobre datos de referencia sin ninguna regla de negocio: no hay nada
que un caso de uso pudiera decidir. Envolverlos añadiría una capa que sólo
reenvía, y multiplicaría por tres el código para ganar uniformidad de diagrama
y nada más. El test `test_las_vistas_no_consultan_el_orm` los excluye
explícitamente, y su nombre dice por qué.

Si mañana un depósito adquiere reglas —horarios de apertura, capacidad
máxima diaria, zonas de cobertura— pasan a caso de uso como el resto.

## Consecuencias

- **Los tests de negocio corren sin base de datos.** 33 tests de dominio y
  casos de uso se ejecutan contra puertos falsos en milisegundos, frente a los
  segundos que cuesta cada test de API.
- **La regla de dependencia está verificada, no prometida.**
  `tests/test_architecture.py` parsea los imports con `ast` y falla si el
  dominio importa Django, si el optimizador importa cualquier cosa, si una
  vista con reglas toca el ORM, o si un caso de uso envuelve a otro.
- **Cambiar de heurística es escribir otro adaptador.** El `RoutePlanner` es un
  puerto; `ClarkeWrightPlanner` es una implementación. Eso hace cierta la
  promesa del ADR 0001.
- **Cuesta una capa de traducción.** `infrastructure/mappers.py` son ~130
  líneas que antes no existían, y cada campo nuevo hay que declararlo en dos
  sitios. Es el precio, y está pagado a conciencia.
- **Los serializers dejaron de ser `ModelSerializer`.** Hay que declarar los
  campos a mano; a cambio la API dejó de moverse cuando se mueve el esquema.

## Alternativas descartadas

**Dejarlo como estaba.** Es la organización que la mayoría de los equipos
Django considera suficiente, y para un CRUD lo es. Aquí no: el núcleo es un
solver con reglas propias, y esas reglas merecen poder probarse sin una base
de datos detrás.

**Un framework de inyección de dependencias.** El grafo es lineal y tiene doce
casos de uso; una raíz de composición explícita de cien líneas se lee mejor
que un contenedor con magia, y se puede reemplazar sin tocar el dominio.
