# El ruleset de AWS es lo que hace util a tflint: sin el solo revisa estilo de
# HCL. Con el, comprueba contra el catalogo real de AWS (que un db.t4g.micro
# exista, que un atributo no este inventado, que un valor este en rango).

plugin "aws" {
  enabled = true
  version = "0.44.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}
