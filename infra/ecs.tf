# Computo: Fargate.
#
# Fargate y no EC2 porque aqui no hay nada que ganar administrando instancias:
# ni cargas de trabajo especiales, ni GPU, ni ahorro por reservas a este
# tamano. Se paga un poco mas por vCPU a cambio de no parchear servidores.

resource "aws_ecs_cluster" "principal" {
  name = var.project

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = var.project }
}

# El log group se declara aqui, no se deja que ECS lo cree solo. Si lo crea
# ECS, nace con retencion infinita y los logs se pagan para siempre.
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project}/api"
  retention_in_days = 30

  tags = { Name = "${var.project}-api" }
}

locals {
  # Comun a la task de la API y a la de migraciones: misma imagen, mismos
  # secretos, misma configuracion. Lo unico que cambia es el comando.
  entorno_comun = [
    { name = "DJANGO_DEBUG", value = "0" },
    { name = "DJANGO_ALLOWED_HOSTS", value = join(",", local.allowed_hosts) },
    { name = "CORS_ALLOWED_ORIGINS", value = "https://${aws_cloudfront_distribution.web.domain_name}" },
  ]

  # `secrets` en vez de `environment`: ECS resuelve el valor desde SSM al
  # arrancar y NO queda en la task definition. En la consola se ve el ARN del
  # parametro, nunca el valor.
  secretos_comunes = [
    { name = "DJANGO_SECRET_KEY", valueFrom = aws_ssm_parameter.django_secret_key.arn },
    { name = "DATABASE_URL", valueFrom = aws_ssm_parameter.database_url.arn },
  ]
}

# ---------------------------------------------------------------------------
# La API
# ---------------------------------------------------------------------------

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = 512  # 0.5 vCPU
  memory = 1024 # 1 GB

  # ARM. Mismo rendimiento por ~20% menos, y la imagen de Python es multi-arch.
  runtime_platform {
    cpu_architecture        = "ARM64"
    operating_system_family = "LINUX"
  }

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true

      portMappings = [{ containerPort = 8000, protocol = "tcp" }]

      environment = local.entorno_comun
      secrets     = local.secretos_comunes

      # Fargate IGNORA el HEALTHCHECK del Dockerfile. Si se quiere sonda a
      # nivel de contenedor hay que declararla aqui; si no, la unica
      # comprobacion es la del ALB y una tarea colgada tarda mas en morir.
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 20
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])

  tags = { Name = "${var.project}-api" }
}

resource "aws_ecs_service" "api" {
  name            = "${var.project}-api"
  cluster         = aws_ecs_cluster.principal.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.privada[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false # sale por el NAT; nunca es alcanzable desde fuera
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  # Da margen a que Django arranque antes de contar fallos del health check.
  health_check_grace_period_seconds = 60

  # Despliegue seguro: si la revision nueva no pasa el health check, ECS
  # revierte sola a la anterior en vez de dejar el servicio caido.
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # El listener tiene que existir antes que el servicio, o el registro en el
  # target group falla. Terraform no lo deduce solo.
  depends_on = [aws_lb_listener.http]

  tags = { Name = "${var.project}-api" }
}

# ---------------------------------------------------------------------------
# Migraciones
# ---------------------------------------------------------------------------
#
# Task aparte, ejecutada a mano antes de cada despliegue:
#
#   aws ecs run-task --cluster milkrun \
#     --task-definition milkrun-migrate --launch-type FARGATE \
#     --network-configuration '{"awsvpcConfiguration":{...}}'
#
# Por que no en el arranque del contenedor de la API: con varias tareas, todas
# correrian `migrate` a la vez contra la misma base. Django toma un lock y no
# se corrompe, pero las demas se quedan esperando, no pasan el health check y
# ECS las mata. Migrar es un paso del despliegue, no del arranque.

resource "aws_ecs_task_definition" "migrate" {
  family                   = "${var.project}-migrate"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = 256
  memory = 512

  runtime_platform {
    cpu_architecture        = "ARM64"
    operating_system_family = "LINUX"
  }

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "migrate"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true
      command   = ["python", "manage.py", "migrate", "--no-input"]

      environment = local.entorno_comun
      secrets     = local.secretos_comunes

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migrate"
        }
      }
    }
  ])

  tags = { Name = "${var.project}-migrate" }
}
