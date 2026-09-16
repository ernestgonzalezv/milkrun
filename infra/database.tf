# Postgres gestionado.
#
# Version 17 para que coincida con la imagen postgres:17-alpine del
# docker-compose. Que la base de desarrollo y la de produccion sean mayores
# distintas es una de las formas mas tontas de que algo pase los tests y
# falle desplegado.

resource "aws_db_subnet_group" "principal" {
  name        = "${var.project}-db"
  description = "Subnets privadas donde puede vivir la instancia"
  subnet_ids  = aws_subnet.privada[*].id

  tags = { Name = "${var.project}-db" }
}

# La contrasena no se escribe en ningun sitio: se genera aqui y se guarda en
# Parameter Store. Yo no la se, y no esta en el repo.
#
# Advertencia honesta: SI queda en texto plano en el tfstate. Por eso el estado
# va en S3 cifrado y nunca a git. No hay forma de evitarlo con Terraform; lo
# unico que se puede hacer es saberlo y tratarlo en consecuencia.
resource "random_password" "db" {
  length = 32
  # RDS rechaza estos caracteres en la contrasena maestra.
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_instance" "principal" {
  identifier = "${var.project}-db"

  engine         = "postgres"
  engine_version = "17"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 50 # autoscaling de disco: evita quedarse sin espacio a las 3am
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.principal.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false # redundante con la subnet privada, pero explicito

  # Sin esto un snapshot pierde el tag Project, y la cuenta es prestada: todo
  # lo que quede vivo tiene que ser rastreable con un solo filtro.
  copy_tags_to_snapshot = true

  # Permite conectarse con credenciales temporales de IAM en vez de la
  # contrasena maestra. No cuesta nada tenerlo encendido.
  iam_database_authentication_enabled = true

  backup_retention_period = 7
  backup_window           = "06:00-07:00" # 02:00 en La Habana, fuera de la jornada de reparto
  maintenance_window      = "sun:07:00-sun:08:00"

  # Multi-AZ apagado a proposito: duplica el precio y esto es una demo.
  # Queda anotado en el README como limitacion conocida, no escondido.
  multi_az = false

  # Una demo se borra y se vuelve a crear. En un entorno real esto seria
  # deletion_protection = true y skip_final_snapshot = false.
  deletion_protection = false
  skip_final_snapshot = true

  # Sin esto, cada `terraform plan` propone cambiar la version en cuanto AWS
  # publica un parche menor, y el plan nunca sale limpio.
  auto_minor_version_upgrade = true

  performance_insights_enabled    = false # cuesta extra y no hace falta aqui
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = { Name = "${var.project}-db" }
}
