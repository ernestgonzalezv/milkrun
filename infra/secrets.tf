# Secretos en SSM Parameter Store, no en la task definition.
#
# Por que Parameter Store y no Secrets Manager: hace lo mismo para este caso
# (SecureString cifrado con KMS, leido por la task via su rol de ejecucion) y
# es gratis en el tier estandar, mientras que Secrets Manager cobra ~0.40 USD
# por secreto al mes. Secrets Manager valdria la pena si hiciera falta rotacion
# automatica; aqui no.
#
# Lo importante no es cual de los dos: es que el valor NO aparece como variable
# de entorno en texto plano en la task definition. Si estuviera ahi, cualquiera
# con permiso de lectura sobre ECS ve la contrasena de la base en la consola.

resource "aws_ssm_parameter" "django_secret_key" {
  name        = "/${var.project}/${var.environment}/DJANGO_SECRET_KEY"
  description = "SECRET_KEY de Django. settings.py revienta si falta y DEBUG=0."
  type        = "SecureString"
  value       = random_password.django_secret_key.result

  tags = { Name = "${var.project}-django-secret-key" }
}

resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

# La URL completa, ya montada, porque settings.py usa dj_database_url y espera
# exactamente este formato. Armarla aqui evita que el contenedor tenga que
# concatenar cuatro variables y equivocarse en el escapado.
resource "aws_ssm_parameter" "database_url" {
  name        = "/${var.project}/${var.environment}/DATABASE_URL"
  description = "URL de conexion que consume dj_database_url en settings.py"
  type        = "SecureString"

  value = format(
    "postgres://%s:%s@%s:%s/%s",
    var.db_username,
    urlencode(random_password.db.result),
    aws_db_instance.principal.address,
    aws_db_instance.principal.port,
    var.db_name,
  )

  tags = { Name = "${var.project}-database-url" }
}
