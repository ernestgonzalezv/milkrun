# Security groups: el firewall de verdad.
#
# La regla de oro esta en que ningun grupo abre puertos a un rango de IPs
# interno. Se referencian ENTRE ELLOS:
#
#   internet ──:443──▶ [alb] ──:8000──▶ [ecs] ──:5432──▶ [rds]
#
# Leido en voz alta: "al 5432 de la base solo entra lo que este en el grupo de
# ECS". No "lo que venga de 10.20.10.0/24". La diferencia importa: si manana
# cambia el direccionamiento, la regla sigue siendo correcta sola, y ningun
# recurso nuevo que alguien meta en esa subnet hereda acceso a la base.
#
# Las reglas van en recursos aparte (aws_vpc_security_group_*_rule) y no en
# bloques `ingress` dentro del security group. Con los bloques inline, si algo
# externo toca una regla, Terraform la revierte entera en el siguiente apply;
# ademas cada regla tiene su propio id y se puede etiquetar.

# ---------------------------------------------------------------------------
# ALB: lo unico que da la cara a internet
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${var.project}-alb"
  description = "Entrada publica HTTP/HTTPS hacia el balanceador"
  vpc_id      = aws_vpc.principal.id

  tags = { Name = "${var.project}-alb" }
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS publico"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# El 80 esta abierto solo para redirigir a 443, no para servir. La redireccion
# la hace el listener del ALB, no la app: asi el trafico en claro nunca llega
# al contenedor.
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP publico, solo para redirigir a HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_hacia_ecs" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Solo hacia las tareas de la API"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# ---------------------------------------------------------------------------
# ECS: el contenedor de Django
# ---------------------------------------------------------------------------

resource "aws_security_group" "ecs" {
  name        = "${var.project}-ecs"
  description = "Tareas Fargate de la API"
  vpc_id      = aws_vpc.principal.id

  tags = { Name = "${var.project}-ecs" }
}

resource "aws_vpc_security_group_ingress_rule" "ecs_desde_alb" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Gunicorn, solo desde el ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

# Salida abierta, y aqui si hay una razon concreta: la tarea tiene que llegar a
# ECR (bajar la imagen), a SSM (leer los secretos) y a CloudWatch (mandar los
# logs), todos con rangos de IP de AWS que cambian. Cerrarlo por CIDR seria
# adivinar. La forma correcta de cerrarlo es con VPC Endpoints -> ver el README.
resource "aws_vpc_security_group_egress_rule" "ecs_salida" {
  security_group_id = aws_security_group.ecs.id
  description       = "Salida via NAT hacia ECR, SSM y CloudWatch"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ---------------------------------------------------------------------------
# RDS: la base de datos
# ---------------------------------------------------------------------------

resource "aws_security_group" "rds" {
  name        = "${var.project}-rds"
  description = "Postgres, alcanzable solo desde las tareas de la API"
  vpc_id      = aws_vpc.principal.id

  tags = { Name = "${var.project}-rds" }
}

resource "aws_vpc_security_group_ingress_rule" "rds_desde_ecs" {
  security_group_id            = aws_security_group.rds.id
  description                  = "Postgres, solo desde ECS"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# A proposito no hay regla de egress para RDS. Sin ninguna regla de salida, el
# grupo no deja salir nada, que es justo lo que se quiere: una base de datos no
# tiene por que iniciar conexiones hacia ningun lado.
