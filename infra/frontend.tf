# El dashboard: build estatico de Vite en S3, servido por CloudFront.
#
# El bucket es PRIVADO. No tiene hosting de sitio web estatico activado ni
# politica publica. La unica forma de leerlo es a traves de CloudFront, que se
# identifica con un Origin Access Control firmado con SigV4.
#
# Asi se evita el fallo mas comun de este montaje: un bucket con
# "Static website hosting" y acceso publico, que se puede leer saltandose el
# CDN (y por tanto saltandose el WAF, el logging y el cache).

resource "aws_s3_bucket" "web" {
  # El nombre de bucket es global en todo AWS. Con el id de cuenta no colisiona
  # con el de nadie y sigue siendo predecible, a diferencia de un sufijo random
  # que cambia el nombre si alguien recrea el estado.
  bucket = "${var.project}-web-${data.aws_caller_identity.actual.account_id}"

  # Una demo se borra entera. En un entorno real esto seria false.
  force_destroy = true

  tags = { Name = "${var.project}-web" }
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket = aws_s3_bucket.web.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "web" {
  bucket = aws_s3_bucket.web.id
  versioning_configuration {
    # Un deploy malo del dashboard se revierte volviendo a la version anterior
    # del objeto, sin reconstruir nada.
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "web" {
  bucket = aws_s3_bucket.web.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# El versionado de arriba guarda cada build del dashboard para siempre. Sin una
# regla de caducidad el bucket crece sin techo y se paga almacenamiento por
# versiones que nadie va a restaurar.
resource "aws_s3_bucket_lifecycle_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    id     = "caducar-versiones-viejas"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_cloudfront_origin_access_control" "web" {
  name                              = "${var.project}-web"
  description                       = "Solo CloudFront puede leer el bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# La politica del bucket no nombra a nadie publico: autoriza al servicio de
# CloudFront Y ademas exige que la peticion venga de ESTA distribucion
# concreta. Sin la condicion del SourceArn, cualquier distribucion de
# CloudFront de cualquier cuenta de AWS podria leer el bucket.
data "aws_iam_policy_document" "web" {
  statement {
    sid       = "SoloEstaDistribucionDeCloudFront"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.web.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.web.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id
  policy = data.aws_iam_policy_document.web.json
}

resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  default_root_object = "index.html"
  comment             = "${var.project} dashboard"

  # Norteamerica y Europa. La clase que incluye Asia y Sudamerica cuesta mas y
  # aqui no hay usuarios que lo justifiquen.
  price_class = "PriceClass_100"

  origin {
    origin_id                = "s3-web"
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.web.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-web"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # Politicas gestionadas por AWS, por id fijo (son globales e iguales en
    # todas las cuentas). CachingOptimized y CORS-S3Origin.
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    origin_request_policy_id   = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"
    response_headers_policy_id = "67f7725c-6f97-4210-82d7-5512b31e9d03" # SecurityHeadersPolicy
  }

  # Enrutado de SPA. React Router maneja /rutas/12 en el cliente, pero ese
  # objeto no existe en S3: S3 devuelve 403 (no 404, porque ListBucket esta
  # denegado). Se traduce a index.html con 200 y el router se encarga.
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Sin dominio propio se usa el certificado por defecto de *.cloudfront.net,
  # que ya da HTTPS valido gratis. Con dominio habria que pasar un ACM emitido
  # en us-east-1, que es un requisito de CloudFront y no de la region elegida.
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = { Name = "${var.project}-web" }
}
