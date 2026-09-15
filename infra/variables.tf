# Entradas de la infraestructura.
#
# Regla que se sigue aqui: tiene default lo que es una decision de diseno ya
# tomada (el CIDR, el tamano de la instancia). NO tiene default lo que es
# especifico de quien aplica (el owner, la cuenta), para que Terraform falle
# pidiendolo en vez de crear recursos con el nombre de otra persona.

variable "project" {
  description = "Prefijo de todos los nombres de recursos. Permite borrar todo filtrando por el."
  type        = string
  default     = "milkrun"
}

variable "environment" {
  description = "Entorno logico. Aqui solo existe 'demo': no hay staging que mantener."
  type        = string
  default     = "demo"
}

variable "owner" {
  description = "Quien aplico esto. Va en los tags; la cuenta es prestada y tiene que ser rastreable."
  type        = string
}

variable "github_owner" {
  description = "Usuario de GitHub, solo para el tag Repo."
  type        = string
}

variable "aws_region" {
  description = "Region. us-east-1 por ser la mas barata y la que tiene todo disponible."
  type        = string
  default     = "us-east-1"
}

# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "Rango privado de la VPC. /16 da 65k direcciones: de sobra y no choca con nada."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "vpc_cidr tiene que ser un CIDR valido, por ejemplo 10.20.0.0/16."
  }
}

variable "az_count" {
  description = <<-EOT
    Zonas de disponibilidad a ocupar.
    Dos es el minimo real: un ALB exige subnets en al menos dos AZ, no es opcional.
  EOT
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count entre 2 y 3. Menos de 2 no lo acepta el ALB; mas de 3 no aporta nada aqui."
  }
}

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

variable "db_instance_class" {
  description = "Tamano de RDS. db.t4g.micro (ARM) es lo mas barato que sirve para la demo."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "Nombre de la base dentro de la instancia."
  type        = string
  default     = "milkrun"
}

variable "db_username" {
  description = "Usuario maestro. La contrasena no se declara: se genera y va a Parameter Store."
  type        = string
  default     = "milkrun"
}

# ---------------------------------------------------------------------------
# Aplicacion
# ---------------------------------------------------------------------------

variable "api_image_tag" {
  description = "Tag de la imagen en ECR que corre la task. Se mueve en cada deploy."
  type        = string
  default     = "latest"
}

variable "api_desired_count" {
  description = "Tareas de la API en paralelo. Una basta para la demo; el codigo aguanta mas."
  type        = number
  default     = 1
}

# ---------------------------------------------------------------------------
# Control de gasto
# ---------------------------------------------------------------------------

variable "budget_limit_usd" {
  description = <<-EOT
    Umbral mensual de la alarma de gasto.
    La cuenta no es mia: esto se crea ANTES que cualquier otra cosa que cueste.
  EOT
  type        = number
  default     = 10
}

# ---------------------------------------------------------------------------
# Dominio (opcional)
# ---------------------------------------------------------------------------
#
# Sin dominio propio no hay certificado de ACM posible: la validacion exige
# demostrar control del DNS. En vez de fingir HTTPS, el stack se adapta:
# con dominio monta ACM y redireccion 80->443; sin dominio se queda en HTTP
# y lo dice en los outputs.

variable "domain_name" {
  description = "Dominio de la API, por ejemplo api.milkrun.dev. Vacio = solo HTTP."
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Zona hospedada donde validar el certificado. Obligatoria si hay domain_name."
  type        = string
  default     = ""

  validation {
    condition     = var.domain_name == "" || var.route53_zone_id != ""
    error_message = "Si se define domain_name hace falta route53_zone_id para validar el certificado de ACM."
  }
}

variable "alert_email" {
  description = "Correo que recibe las alarmas y los avisos de presupuesto."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "alert_email tiene que ser una direccion de correo valida."
  }
}
