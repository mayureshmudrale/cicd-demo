data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.network_id]
  }
  filter {
    name   = "tag:Access"
    values = ["private"]
  }
}

resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = data.aws_subnets.private.ids
  tags       = { Name = var.name }
}

resource "aws_security_group" "this" {
  name        = "${var.name}-rds"
  description = "Postgres access for ${var.name}"
  vpc_id      = var.network_id

  dynamic "ingress" {
    for_each = var.allowed_from
    content {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-rds" }
}

resource "random_password" "master" {
  length  = 32
  special = false # some special chars aren't valid in an RDS master password; keep this simple and let a rotation step layer complexity on top if ever needed
}

resource "aws_db_instance" "this" {
  identifier     = var.name
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.db_class

  allocated_storage = var.storage_gb
  storage_encrypted = true

  db_name  = "ideaboard"
  username = "ideaboard"
  password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.this.id]
  multi_az               = var.ha

  # Belt and suspenders with the security group above: database_never_public
  # is enforced at the resource level too, not just via network access rules.
  publicly_accessible = false

  # POC default: a real deployment should drop this (and let `terraform
  # destroy` take a final snapshot) rather than skip it unconditionally.
  skip_final_snapshot = true
}
