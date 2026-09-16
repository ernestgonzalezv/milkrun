# infra

Terraform de la infraestructura de milkrun en AWS.

> **Esto no esta aplicado en una cuenta AWS real.** Se escribio y se valida en
> CI con `terraform fmt`, `terraform validate`, `tflint` (ruleset de AWS) y
> `checkov`, todo sin credenciales. No hay un `apply` detras, y los numeros de
> costo de mas abajo son estimaciones de la calculadora, no de una factura.
> Se dice aqui arriba para que nadie tenga que deducirlo.

## La forma

```
                        internet
                            │
              ┌─────────────┴──────────────┐
              │                            │
        CloudFront                        ALB              subnets publicas
        (dashboard)                   (HTTP/HTTPS)
              │                            │
         S3 privado                   ECS Fargate          subnets privadas
       (build de Vite)                 (Django)                 sin IP publica
                                           │
                                    ┌──────┴──────┐
                                    │             │
                              RDS Postgres   SSM Parameter Store
                                                (secretos)
```

Nada que no tenga que atender internet es alcanzable desde internet. ECS y RDS
viven en subnets privadas y salen por un NAT Gateway, que deja salir y no deja
entrar. Los security groups se referencian entre ellos en vez de abrir rangos
de IP: la regla de Postgres dice *"solo el grupo de ECS"*, no *"10.20.10.0/24"*,
asi que sigue siendo correcta si cambia el direccionamiento y ningun recurso
nuevo en esa subnet hereda acceso a la base.

## Archivos

| Archivo | Que hay |
|---|---|
| `versions.tf` | Versiones fijadas, backend de S3 (comentado, ver abajo) |
| `providers.tf` | `default_tags` para que todo sea rastreable y borrable |
| `variables.tf` | Entradas, con `validation` en las que tienen reglas reales |
| `network.tf` | VPC, subnets, IGW, NAT, tablas de rutas |
| `security_groups.tf` | Los tres grupos encadenados: alb → ecs → rds |
| `database.tf` | Postgres 17, contrasena generada, nunca escrita |
| `secrets.tf` | Parameter Store con `SecureString` |
| `registry.tf` | ECR con tags inmutables y politica de ciclo de vida |
| `iam.tf` | Rol de ejecucion y rol de tarea, separados y acotados |
| `alb.tf` | Balanceador, target group y HTTPS condicional |
| `ecs.tf` | Cluster, task de la API, task de migraciones, servicio |
| `frontend.tf` | S3 privado + CloudFront con Origin Access Control |
| `observability.tf` | Log groups, alarmas y presupuesto |
| `outputs.tf` | URLs, comando de migracion, verificacion del destroy |

## Decisiones

**Los dos roles de IAM estan separados.** El de ejecucion lo usa el agente de
ECS antes de que arranque el codigo: baja la imagen y lee los secretos. El de
tarea lo usa Django ya corriendo. Separarlos significa que si alguien logra
ejecutar codigo dentro del contenedor, **no puede pedir mas parametros de SSM**:
recibio los suyos inyectados, pero no tiene el permiso. Los recursos estan
enumerados ARN por ARN, no con `parameter/*`.

**Los secretos van en `secrets`, no en `environment`.** Un valor en
`environment` se ve en texto plano en la consola de ECS para cualquiera con
permiso de lectura. En `secrets` solo se ve el ARN del parametro.

**Las migraciones son una task aparte.** Si corrieran al arrancar el
contenedor, con varias tareas todas ejecutarian `migrate` contra la misma base:
Django toma un lock y no se corrompe, pero las demas esperan, no pasan el
health check y ECS las mata. Migrar es un paso del despliegue, no del arranque.

**El ALB comprueba `/healthz` y no `/readyz`.** `/healthz` no toca la base. Si
la sonda dependiera de Postgres, una caida de RDS tumbaria el health check de
todas las tareas, ECS las mataria, y al volver la base no quedaria ninguna viva:
un incidente de la base se convertiria en una caida total. Ver
`backend/apps/shared/health.py`.

**HTTPS es condicional.** Sin dominio propio no hay certificado de ACM posible
—la validacion exige demostrar control del DNS—, asi que el stack se queda en
HTTP y el output lo dice. El dashboard si tiene HTTPS: el certificado por
defecto de `*.cloudfront.net` es valido y gratis.

**El bucket del dashboard es privado.** Sin hosting de sitio estatico y sin
politica publica: solo lo lee CloudFront via Origin Access Control, y la
politica exige ademas que venga de *esta* distribucion (`AWS:SourceArn`). Sin
esa condicion, cualquier distribucion de CloudFront de cualquier cuenta de AWS
podria leer el bucket.

**El estado remoto esta comentado.** Problema de huevo y gallina: el bucket que
guarda el estado tiene que existir antes del primer `apply`. Se aplica una vez
con estado local y se migra con `terraform init -migrate-state`. `use_lockfile`
sustituye a la tabla de DynamoDB que hacia falta antes para el bloqueo.

> **El `tfstate` contiene la contrasena de RDS en texto plano.** No hay forma de
> evitarlo en Terraform. Por eso el estado va cifrado en S3 y nunca a git.

## Que NO se uso, y por que

Esta lista importa tanto como la de arriba.

| Servicio | Por que no |
|---|---|
| **EKS** | Kubernetes para un contenedor. El coste de operacion supera cualquier beneficio a este tamano. |
| **Lambda** | Ya hay una imagen de contenedor que funciona y esta probada. Meter un segundo modelo de ejecucion es complejidad sin problema que la pida. |
| **ElastiCache** | No hay ningun problema de latencia medido. Cachear antes de medir es adivinar. |
| **DynamoDB** | El dominio es relacional: paradas, rutas, vehiculos, conductores. Postgres ya lo resuelve. |
| **Secrets Manager** | Hace lo mismo que Parameter Store para este caso y cobra ~0.40 USD por secreto al mes. Valdria la pena si hiciera falta rotacion automatica. |
| **VPC Endpoints** | Serian **mejor** que el NAT: el trafico a ECR, SSM y CloudWatch no saldria a internet. Se descartaron por volumen de codigo, no porque el NAT sea superior. Es la primera mejora si esto fuera a produccion. |
| **CloudFront delante de la API** | El dashboard se beneficia de un CDN; una API con escrituras no. Ademas la app Android consume la misma API y no deberia pasar por un CDN. |
| **WAF** | Cuesta ~5 USD/mes de base y aqui no hay trafico que defender. Iria en produccion real. |
| **Multi-AZ en RDS / un NAT por AZ** | Duplican el precio de las dos piezas mas caras. Ambas quedan anotadas abajo como limitaciones. |

## Checkov: 169 pasan, 6 arreglados, 29 justificados

El job de CI falla si aparece un hallazgo que no este en esta tabla. La lista de
`skip_check` del workflow no es un silenciador: es un acuerdo escrito, y cada
linea de abajo tiene que sostenerse sola.

### Arreglados, porque eran reales y baratos

| Check | Que se hizo |
|---|---|
| `CKV2_AWS_12` | El security group por defecto de la VPC se declara vacio. AWS lo crea permitiendo todo el trafico entre sus miembros, y cualquier recurso creado sin grupo explicito cae ahi. |
| `CKV_AWS_130` | Las subnets publicas dejan de asignar IP publica automatica. Lo que las hace publicas es su tabla de rutas; el ALB trae sus propias IPs y el NAT usa una Elastic IP. |
| `CKV2_AWS_60` | RDS copia los tags a los snapshots. La cuenta es prestada y todo lo que quede vivo tiene que salir con un solo filtro. |
| `CKV_AWS_161` | Autenticacion IAM en RDS. Permite credenciales temporales en vez de la contrasena maestra, y no cuesta nada. |
| `CKV_AWS_26` | El topico SNS va cifrado con la clave gestionada de AWS. |
| `CKV2_AWS_61` | Caducidad de versiones antiguas en S3. El bucket tiene versionado; sin regla de expiracion crece sin techo y se paga almacenamiento de builds que nadie va a restaurar. |

### Excluidos: cuestan dinero en un stack que nunca se enciende

`CKV2_AWS_11` flow logs de VPC · `CKV_AWS_118` monitorizacion mejorada de RDS ·
`CKV_AWS_353` performance insights · `CKV2_AWS_30` query logging de Postgres ·
`CKV_AWS_86` logs de CloudFront · `CKV_AWS_91` logs del ALB ·
`CKV2_AWS_28` `CKV_AWS_68` `CKV2_AWS_47` WAF

Todos son correctos en produccion. WAF son ~5 USD/mes de base y los logs se pagan
por ingesta. Este stack no atiende trafico, asi que pagarian por nada.

### Excluidos: necesitan un dominio propio

`CKV2_AWS_20` redireccion HTTP a HTTPS · `CKV_AWS_103` TLS 1.2 en el balanceador ·
`CKV_AWS_378` el ALB no debe usar HTTP · `CKV_AWS_260` entrada 0.0.0.0/0 al puerto 80 ·
`CKV2_AWS_42` certificado propio en CloudFront · `CKV_AWS_174` TLS 1.2 en CloudFront

ACM valida por DNS, y sin control de una zona no hay certificado posible. El stack se
adapta: con `domain_name` monta ACM, redireccion y politica TLS 1.3; sin el se queda
en HTTP y el output lo dice. En cuanto se define la variable, estos seis dejan de
fallar solos.

### Excluidos: decisiones de demo, ya en Limitaciones conocidas

`CKV_AWS_150` proteccion de borrado del ALB · `CKV_AWS_293` proteccion de borrado de RDS ·
`CKV_AWS_157` Multi-AZ en RDS

Las dos primeras harian que `terraform destroy` fallara y obligara a ir a la consola.
Multi-AZ duplica el precio de la pieza mas cara.

### Excluidos: clave gestionada por AWS en vez de CMK propia

`CKV_AWS_136` ECR · `CKV_AWS_145` S3 · `CKV_AWS_158` CloudWatch Logs · `CKV_AWS_337` SSM

Todo esta cifrado en reposo; lo que checkov pide es una clave gestionada por el
cliente. Una CMK cuesta 1 USD al mes y trae rotacion, politica y el riesgo de
perder el acceso a los datos si se borra. Para datos de demo el reparto no compensa.

### Excluidos: no aplican a esta arquitectura

| Check | Por que |
|---|---|
| `CKV2_AWS_62` | Notificaciones de evento en S3. El bucket sirve un build estatico; no hay nada que reaccione a una subida. |
| `CKV_AWS_310` | Failover de origen en CloudFront. Hay un solo origen. |
| `CKV_AWS_374` | Restriccion geografica. Un panel de reparto no tiene motivo para bloquear paises. |
| `CKV2_AWS_32` | Politica de cabeceras de respuesta. **Si esta puesta** (`SecurityHeadersPolicy` por su id gestionado); checkov no resuelve politicas gestionadas por id. |
| `CKV_AWS_336` | Raiz de solo lectura en ECS. Fargate no soporta `tmpfs`, y gunicorn necesita escribir en `/tmp`. |

## Limitaciones conocidas

Decisiones con su coste a la vista, no pendientes escondidos.

- **Un solo NAT Gateway para las dos AZ.** Si se cae esa zona, las tareas de la
  otra se quedan sin salida. Lo correcto en produccion es uno por zona.
- **RDS sin Multi-AZ.** Una caida de la instancia es una caida del servicio, y
  la recuperacion depende del backup diario.
- **Sin autoscaling.** `desired_count` es fijo. El codigo aguanta mas de una
  tarea; simplemente no hay politica de escalado declarada.
- **El despliegue no esta automatizado.** No hay workflow de `apply`: haria
  falta OIDC entre GitHub y AWS, y sin cuenta real no habia forma de probarlo.
- **La validacion de CI no es un `plan`.** `validate` y `tflint` detectan
  sintaxis, referencias y atributos invalidos; no detectan que un `apply`
  fallaria por un limite de la cuenta o un permiso que falte.

## Uso

```bash
brew install terraform tflint
cp terraform.tfvars.example terraform.tfvars   # rellenar

terraform init -backend=false
terraform fmt -check -recursive
terraform validate
tflint --init && tflint
```

Con credenciales, el ciclo completo seria:

```bash
terraform apply
aws ecs run-task ...                  # ver el output `comando_migrar`
docker build --platform linux/arm64 -t $ECR:$TAG backend/ && docker push $ECR:$TAG
aws s3 sync web/dist/ s3://$BUCKET/   # dashboard

terraform destroy
aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=milkrun
# ^ debe devolver lista vacia
```
