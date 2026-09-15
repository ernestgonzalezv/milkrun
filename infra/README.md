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
