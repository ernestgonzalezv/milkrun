# `default_tags` aplica estas etiquetas a TODO recurso que soporte tags, sin
# repetirlas recurso por recurso.
#
# No es cosmetico: la cuenta de AWS es prestada, asi que cualquiera tiene que
# poder responder "que es esto y quien lo creo" mirando la consola, y filtrar
# por Project=milkrun para auditar o para verificar que el destroy no dejo
# nada vivo.

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      Repo        = "github.com/${var.github_owner}/milkrun"
    }
  }
}
