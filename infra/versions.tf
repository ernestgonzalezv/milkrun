# Versiones fijadas a lo que esta probado, igual que el resto del proyecto.
#
# El backend remoto esta comentado a proposito: hay un problema de huevo y
# gallina. El bucket que guarda el estado tiene que existir ANTES del primer
# apply, asi que el primer apply se hace con estado local y despues se migra
# con `terraform init -migrate-state`.
#
# `use_lockfile` reemplaza a la tabla de DynamoDB que se usaba antes para el
# bloqueo: S3 ya sabe hacerlo solo desde Terraform 1.10.

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # backend "s3" {
  #   bucket       = "milkrun-tfstate"
  #   key          = "infra/terraform.tfstate"
  #   region       = "us-east-1"
  #   encrypt      = true
  #   use_lockfile = true
  # }
}
