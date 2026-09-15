# Permisos. Esta es la parte donde de verdad se ve si alguien sabe AWS.
#
# Hay DOS roles y confundirlos es el error clasico:
#
#   execution_role  ->  lo usa el AGENTE de ECS, antes de que tu codigo arranque.
#                       Baja la imagen de ECR, lee los secretos, abre el log group.
#   task_role       ->  lo usa TU CODIGO, ya corriendo. Es lo que puede hacer
#                       Django con boto3 desde dentro del contenedor.
#
# Separarlos es lo que permite que el contenedor NO pueda leer los secretos de
# SSM por su cuenta: los recibe inyectados como variables de entorno, pero si
# alguien logra ejecutar codigo dentro, no puede pedir mas parametros.

data "aws_caller_identity" "actual" {}

# ---------------------------------------------------------------------------
# Rol de ejecucion: para el agente de ECS
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    # Evita el problema del "confused deputy": limita que este rol solo se
    # pueda asumir en nombre de tareas de ESTA cuenta, no de una ajena.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.actual.account_id]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project}-ecs-execution"
  description        = "Lo asume el agente de ECS para arrancar la tarea"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = { Name = "${var.project}-ecs-execution" }
}

# Politica gestionada por AWS: pull de ECR y escritura en CloudWatch Logs.
# Se usa la de AWS porque esta bien acotada y la mantienen ellos.
resource "aws_iam_role_policy_attachment" "ecs_execution_base" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Lo que la politica de AWS no cubre: leer los secretos concretos de esta app.
# Fijate que los recursos estan enumerados uno por uno. Nada de
# "arn:aws:ssm:*:*:parameter/*", que es lo que sale en los tutoriales y le da
# a este rol acceso a los secretos de cualquier otra app de la cuenta.
data "aws_iam_policy_document" "ecs_execution_secretos" {
  statement {
    sid     = "LeerSoloLosSecretosDeEstaApp"
    actions = ["ssm:GetParameters"]
    resources = [
      aws_ssm_parameter.django_secret_key.arn,
      aws_ssm_parameter.database_url.arn,
    ]
  }

  statement {
    sid     = "DescifrarSecureString"
    actions = ["kms:Decrypt"]
    # La clave gestionada de AWS para SSM. Sin esto, GetParameters devuelve
    # AccessDenied sobre un SecureString y el error no dice que falta KMS.
    resources = ["arn:aws:kms:${var.aws_region}:${data.aws_caller_identity.actual.account_id}:alias/aws/ssm"]
  }
}

resource "aws_iam_role_policy" "ecs_execution_secretos" {
  name   = "${var.project}-leer-secretos"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_secretos.json
}

# ---------------------------------------------------------------------------
# Rol de la tarea: para el codigo de Django
# ---------------------------------------------------------------------------

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project}-ecs-task"
  description        = "Lo asume el proceso de Django ya en ejecucion"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json

  tags = { Name = "${var.project}-ecs-task" }
}

# Hoy Django solo necesita escribir los estaticos del admin en S3. Nada mas.
# Si manana aparecen fotos de prueba de entrega, se anade aqui y se ve en el
# diff exactamente que permiso nuevo gano la aplicacion.
data "aws_iam_policy_document" "ecs_task" {
  statement {
    sid     = "EstaticosDelAdmin"
    actions = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
    # Solo objetos DENTRO del prefijo static/. No el bucket entero.
    resources = ["${aws_s3_bucket.web.arn}/static/*"]
  }

  statement {
    sid       = "ListarSoloEsePrefijo"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.web.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["static/*"]
    }
  }
}

resource "aws_iam_role_policy" "ecs_task" {
  name   = "${var.project}-tarea"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task.json
}
