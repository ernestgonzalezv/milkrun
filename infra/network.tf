# La red. Tres capas, de fuera hacia dentro:
#
#   internet ──▶ subnets publicas   solo el ALB vive aqui
#                     │
#                     ▼
#                subnets privadas   ECS y RDS, sin IP publica
#                     │
#                     ▼
#                NAT Gateway        deja SALIR, no deja ENTRAR
#
# La idea de fondo: nada que no tenga que atender internet debe ser alcanzable
# desde internet. El contenedor de Django igual necesita salir (bajar la imagen
# de ECR, leer secretos de SSM), y para eso esta el NAT.

data "aws_availability_zones" "disponibles" {
  state = "available"
}

resource "aws_vpc" "principal" {
  cidr_block = var.vpc_cidr

  # Hacen falta las dos para que RDS resuelva su endpoint por nombre dentro de
  # la VPC. Sin esto el contenedor no encuentra la base de datos.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project}-vpc" }
}

# ---------------------------------------------------------------------------
# Subnets
# ---------------------------------------------------------------------------
#
# El reparto del /16 se calcula, no se escribe a mano:
#
#   cidrsubnet("10.20.0.0/16", 8, 0)  ->  10.20.0.0/24   publica  AZ a
#   cidrsubnet("10.20.0.0/16", 8, 1)  ->  10.20.1.0/24   publica  AZ b
#   cidrsubnet("10.20.0.0/16", 8, 10) ->  10.20.10.0/24  privada  AZ a
#   cidrsubnet("10.20.0.0/16", 8, 11) ->  10.20.11.0/24  privada  AZ b
#
# El salto a 10 en las privadas es para dejar hueco: si manana hacen falta mas
# subnets publicas, entran sin renumerar nada.

resource "aws_subnet" "publica" {
  count = var.az_count

  vpc_id            = aws_vpc.principal.id
  availability_zone = data.aws_availability_zones.disponibles.names[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)

  # Falso a proposito. Lo que hace publica a esta subnet es su tabla de rutas
  # hacia el IGW, no que reparta IPs automaticamente. Aqui solo vive el ALB,
  # que trae las suyas, y el NAT, que usa una Elastic IP. Asignar IP publica
  # por defecto solo serviria para que algo creado sin pensar quede expuesto.
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project}-publica-${count.index}"
    Tier = "public"
  }
}

resource "aws_subnet" "privada" {
  count = var.az_count

  vpc_id            = aws_vpc.principal.id
  availability_zone = data.aws_availability_zones.disponibles.names[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)

  tags = {
    Name = "${var.project}-privada-${count.index}"
    Tier = "private"
  }
}

# ---------------------------------------------------------------------------
# Salida a internet
# ---------------------------------------------------------------------------

resource "aws_internet_gateway" "principal" {
  vpc_id = aws_vpc.principal.id
  tags   = { Name = "${var.project}-igw" }
}

# Un solo NAT para las dos AZ, no uno por AZ.
#
# Lo correcto en produccion de verdad es uno por zona: con uno solo, si se cae
# esa AZ, las tareas de la otra se quedan sin salida. Aqui es una demo y el NAT
# es de lo mas caro del stack, asi que se acepta el riesgo a proposito.
# Queda anotado en el README como limitacion, no escondido.
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "${var.project}-nat-eip" }
}

resource "aws_nat_gateway" "principal" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.publica[0].id

  # El NAT necesita que el IGW ya exista; Terraform no infiere esa dependencia
  # porque no hay referencia directa entre los dos recursos.
  depends_on = [aws_internet_gateway.principal]

  tags = { Name = "${var.project}-nat" }
}

# ---------------------------------------------------------------------------
# Enrutado
# ---------------------------------------------------------------------------

resource "aws_route_table" "publica" {
  vpc_id = aws_vpc.principal.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.principal.id
  }

  tags = { Name = "${var.project}-rt-publica" }
}

resource "aws_route_table" "privada" {
  vpc_id = aws_vpc.principal.id

  # Misma ruta por defecto, destino distinto: el NAT en vez del IGW. Esa unica
  # linea es toda la diferencia entre "alcanzable desde internet" y "no".
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.principal.id
  }

  tags = { Name = "${var.project}-rt-privada" }
}

resource "aws_route_table_association" "publica" {
  count          = var.az_count
  subnet_id      = aws_subnet.publica[count.index].id
  route_table_id = aws_route_table.publica.id
}

resource "aws_route_table_association" "privada" {
  count          = var.az_count
  subnet_id      = aws_subnet.privada[count.index].id
  route_table_id = aws_route_table.privada.id
}
