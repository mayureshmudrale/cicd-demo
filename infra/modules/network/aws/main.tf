data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = var.name }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = var.name }
}

# Public subnets: the NAT gateway and (if a chart's ingress ever wants one
# directly) a public-facing load balancer. Never anything app/database-facing
# — database_never_public is an enforced invariant, not just a convention.
resource "aws_subnet" "public" {
  count                   = var.az_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${var.name}-public-${count.index}", Access = "public" }
}

# Private subnets: EKS worker nodes and RDS. var.cidr's second half, offset
# past the public range above so the two never overlap regardless of az_count.
resource "aws_subnet" "private" {
  count             = var.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.cidr, 8, count.index + 100)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  # The "Access" tag (not just Name) is what lets the database module find
  # these purely from network_id, via `data "aws_subnets"`, with no extra
  # subnet-id variable needed — keeping the database contract exactly
  # {name, tier, network_id, allowed_from}, same shape as local/gcp.
  tags = { Name = "${var.name}-private-${count.index}", Access = "private" }
}

# One NAT gateway, not one per AZ: the private subnets' only use is EKS
# node egress (image pulls, AWS API calls) and RDS has no egress need at
# all, so a single NAT is a deliberate cost/simplicity tradeoff for this
# tier, not an oversight — revisit per-AZ NAT if a tier ever needs that HA.
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = var.name }
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags          = { Name = var.name }

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = { Name = "${var.name}-public" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = { Name = "${var.name}-private" }
}

resource "aws_route_table_association" "public" {
  count          = var.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = var.az_count
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
