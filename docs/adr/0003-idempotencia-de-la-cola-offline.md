# 0003 - La idempotencia del sync vive en una restriccion de base de datos

Fecha: 2026-09-11
Estado: aceptada

## Contexto

La app movil acumula eventos sin conexion y los reenvia. Un reenvio ocurre
cuando la respuesta se pierde aunque el servidor si haya escrito: el telefono
no puede distinguir "no llego" de "llego y no me entere". La unica politica
sana del lado del cliente es reintentar hasta recibir 2xx.

Eso obliga al servidor a aceptar la misma tanda N veces sin duplicar nada.

## Decision

Cada evento lleva un `client_event_id` (UUID) que **genera el telefono** antes
del primer intento. En la base hay una restriccion unica sobre
`(driver, client_event_id)`.

El servidor inserta y captura `IntegrityError`: si choca, cuenta el evento
como duplicado y sigue. La respuesta siempre es 200 con el desglose
`created` / `duplicates`, nunca un error.

## Consecuencias

- La garantia la da el motor de base de datos, no una comprobacion previa en
  Python. Un `if ya_existe` antes del insert tiene una ventana de carrera
  entre la lectura y la escritura; la restriccion unica no.
- El cliente se simplifica a "reintentar hasta 2xx, despues vaciar la cola".
  No hay logica de reconciliacion en el telefono.
- El identificador es por chofer, no global: dos telefonos distintos no se
  pisan aunque generaran el mismo UUID.
- El mismo patron se aplica a las posiciones GPS, ahi con
  `(driver, recorded_at)`, porque un ping no necesita id propio: su marca de
  tiempo ya lo identifica.

## Alternativas descartadas

**Cabecera `Idempotency-Key` por request.** Es el patron de Stripe y sirve
para una operacion por peticion. Aqui cada peticion trae una tanda, y lo que
hay que deduplicar es cada evento por separado: si la tanda cambia entre dos
intentos (el caso normal, porque el chofer sigue trabajando), una clave por
request no ayuda.

**Deduplicar por `(stop, kind, occurred_at)`.** Fragil: dos eventos legitimos
pueden compartir esos tres valores, y el timestamp del dispositivo puede
cambiar si el reloj se ajusta.
