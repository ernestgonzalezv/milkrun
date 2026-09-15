# Registro de imagenes.
#
# Solo hay uno: la imagen del backend. El dashboard no lleva contenedor porque
# es un build estatico de Vite que va a S3, y la app Android se distribuye como
# APK. Un repositorio por artefacto que de verdad exista.

resource "aws_ecr_repository" "api" {
  name = "${var.project}/api"

  # MUTABLE dejaria que alguien reescriba el tag `latest` apuntando a otra
  # imagen. Con IMMUTABLE, un tag identifica una imagen para siempre: lo que
  # probaste es exactamente lo que corre.
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true # escaneo de CVEs gratis, no hay razon para apagarlo
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = { Name = "${var.project}-api" }
}

# Sin esto el repositorio crece sin limite y se paga almacenamiento por cada
# imagen vieja que nadie va a usar nunca.
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Conservar las ultimas 10 imagenes etiquetadas"
        selection = {
          tagStatus     = "tagged"
          tagPatternList = ["*"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Borrar las sin etiqueta al dia siguiente"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
    ]
  })
}
