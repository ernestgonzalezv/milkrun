---
paths:
  - "infra/**/*.tf"
  - "infra/**/*.hcl"
---

# Infra — Terraform sobre AWS

> **Este stack no esta aplicado en ninguna cuenta de AWS.** Se escribe y se valida sin
> credenciales: `terraform fmt`, `terraform validate`, `tflint` con el ruleset de AWS y
> `checkov`. `terraform apply` y `terraform destroy` estan denegados en `settings.json`.
> Si una tarea parece necesitarlos, para y pregunta.

## Invariantes

- **Nada fuera del ALB y de CloudFront da la cara a internet.** ECS y RDS viven en subnets
  privadas con `assign_public_ip = false` y `publicly_accessible = false`. Si un recurso nuevo
  necesita salir, sale por el NAT; si necesita entrar, entra por el balanceador.
- **Los security groups se referencian entre ellos, nunca por CIDR.** Usa
  `referenced_security_group_id`. Una regla que dice "solo el grupo de ECS" sigue siendo correcta
  cuando cambia el direccionamiento; una que dice `10.20.10.0/24` no, y ademas regala acceso a
  cualquier recurso que alguien meta despues en esa subnet.
- **Las reglas van en recursos aparte** (`aws_vpc_security_group_ingress_rule` /
  `_egress_rule`), no en bloques `ingress`/`egress` inline. Los inline revierten cambios externos
  en bloque y no se pueden etiquetar por separado.
- **Ningun secreto en `environment`.** Van en `secrets` apuntando a SSM Parameter Store. Un valor
  en `environment` se lee en texto plano desde la consola de ECS.
- **IAM enumera ARNs.** Nada de `parameter/*` ni `Resource = "*"`. Los dos roles estan separados
  a proposito: `ecs_execution` lo usa el agente antes de arrancar, `ecs_task` lo usa el codigo ya
  corriendo. No los fusiones.
- **Todo recurso hereda `default_tags`.** La cuenta es prestada: `Project=milkrun` tiene que
  bastar para auditar y para verificar que no quedo nada vivo.

## Cosas que muerden

- `create_before_destroy` con `name` fijo se estrella al reemplazar: el recurso nuevo choca con
  el viejo, que sigue existiendo. Usa `name_prefix` (en target groups son 6 caracteres como
  maximo).
- `$${` en HCL es el escape de un `${` literal, **no** una interpolacion. Para meter un `$`
  delante de una variable usa `format("...$%s", var.x)`.
- Un ALB exige subnets en dos AZ como minimo. No es configurable.
- El NAT Gateway va en subnet **publica**: el mismo necesita la ruta al IGW. En una privada su
  ruta por defecto apuntaria a si mismo.
- Los certificados de ACM para CloudFront tienen que emitirse en `us-east-1`, independientemente
  de la region del resto del stack.
- El `tfstate` guarda la contrasena de RDS en texto plano. No hay forma de evitarlo: por eso va
  cifrado en S3 y nunca a git.

## Al anadir algo

1. Si cuesta dinero por existir y no por usarse (NAT, ALB, endpoints de interfaz), dilo en el
   PR con el numero mensual.
2. Si lo descartas, escribe **por que** en la tabla "Que NO se uso" de `infra/README.md`. Esa
   tabla vale tanto como el codigo.
3. Si introduce una limitacion (una sola AZ, sin autoscaling), va a "Limitaciones conocidas".
   Documentada, no escondida.
4. Corre `terraform fmt -recursive`, `terraform validate -backend=false`, `tflint` y `checkov`
   antes de decir que esta listo. Una excepcion de checkov se justifica en el README, no se
   silencia a ciegas.
