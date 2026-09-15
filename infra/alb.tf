# Balanceador. Es lo unico del stack que da la cara a internet.
#
# Hace tres cosas que el contenedor no deberia hacer:
#   1. Terminar TLS, para que gunicorn hable HTTP en claro dentro de la VPC.
#   2. Repartir entre tareas y sacar de rotacion las que no responden.
#   3. Redirigir 80 -> 443 antes de que el trafico en claro llegue a la app.

locals {
  # HTTPS solo es posible con dominio propio: ACM valida por DNS y sin zona
  # no hay como demostrar el control. La variable manda sobre todo el archivo.
  https_habilitado = var.domain_name != "" && var.route53_zone_id != ""

  # Lo que Django aceptara en el header Host. La IP privada de la tarea se
  # anade sola en tiempo de ejecucion (ver settings.py): el health check del
  # ALB llega con Host = IP del target, que no se conoce desde aqui.
  allowed_hosts = compact([
    aws_lb.principal.dns_name,
    var.domain_name,
  ])
}

resource "aws_lb" "principal" {
  name               = "${var.project}-alb"
  load_balancer_type = "application"
  internal           = false
  subnets            = aws_subnet.publica[*].id
  security_groups    = [aws_security_group.alb.id]

  # Con esto encendido, un `terraform destroy` falla y hay que ir a la consola
  # a apagarlo. En una demo que se crea y se borra estorba mas de lo que ayuda.
  enable_deletion_protection = false

  # Descarta cabeceras HTTP malformadas en vez de pasarlas al backend. Cierra
  # la via de request smuggling, donde el ALB y gunicorn interpretan distinto
  # una cabecera ambigua y acaban viendo dos peticiones diferentes.
  drop_invalid_header_fields = true

  tags = { Name = "${var.project}-alb" }
}

resource "aws_lb_target_group" "api" {
  # name_prefix y no name: con `create_before_destroy` mas abajo, un nombre
  # fijo hace que el target group nuevo choque con el viejo, que todavia
  # existe durante el reemplazo. AWS limita este prefijo a 6 caracteres.
  name_prefix = "ltapi-"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.principal.id

  # "ip" y no "instance": en Fargate no hay EC2 que registrar, el target es
  # directamente la IP de la tarea en la subnet privada.
  target_type = "ip"

  health_check {
    path     = "/healthz" # liveness, no toca la base. Ver apps/shared/health.py
    protocol = "HTTP"
    matcher  = "200"

    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  # Django tarda en arrancar (migraciones ya hechas aparte, pero gunicorn con
  # 3 workers no es instantaneo). 30s de gracia evitan matar tareas sanas.
  deregistration_delay = 30

  # Sin esto, cambiar algo del target group falla porque el listener sigue
  # apuntando al viejo. Terraform crea el nuevo antes de soltar el anterior.
  lifecycle {
    create_before_destroy = true
  }

  tags = { Name = "${var.project}-api" }
}

# ---------------------------------------------------------------------------
# Certificado, solo si hay dominio
# ---------------------------------------------------------------------------

resource "aws_acm_certificate" "api" {
  count = local.https_habilitado ? 1 : 0

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = { Name = "${var.project}-cert" }
}

resource "aws_route53_record" "validacion" {
  for_each = local.https_habilitado ? {
    for opcion in aws_acm_certificate.api[0].domain_validation_options :
    opcion.domain_name => {
      name   = opcion.resource_record_name
      record = opcion.resource_record_value
      type   = opcion.resource_record_type
    }
  } : {}

  zone_id         = var.route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

# Este recurso no crea nada: espera a que ACM confirme la validacion. Sin el,
# el listener HTTPS intentaria usar un certificado todavia PENDING y fallaria.
resource "aws_acm_certificate_validation" "api" {
  count = local.https_habilitado ? 1 : 0

  certificate_arn         = aws_acm_certificate.api[0].arn
  validation_record_fqdns = [for registro in aws_route53_record.validacion : registro.fqdn]
}

# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------

# Puerto 80. Con dominio redirige; sin dominio es la unica entrada que hay.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.principal.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = local.https_habilitado ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = local.https_habilitado ? [] : [1]
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.api.arn
    }
  }
}

resource "aws_lb_listener" "https" {
  count = local.https_habilitado ? 1 : 0

  load_balancer_arn = aws_lb.principal.arn
  port              = 443
  protocol          = "HTTPS"

  # Politica sin TLS 1.0 ni 1.1. La que trae AWS por defecto todavia los acepta.
  ssl_policy      = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn = aws_acm_certificate_validation.api[0].certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
