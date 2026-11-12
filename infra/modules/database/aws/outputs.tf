output "database_url" {
  value     = "postgresql+psycopg://${aws_db_instance.this.username}:${random_password.master.result}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${aws_db_instance.this.db_name}"
  sensitive = true
}

output "host" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

# Backend-specific extras (like cluster/aws's kubernetes_version): local's
# database module never needs these as outputs since CNPG already writes
# an in-cluster secret directly. aws/gcp need them so the live root can
# build that same-shaped secret itself from a managed DB with no
# equivalent operator.
output "username" {
  value = aws_db_instance.this.username
}

output "db_name" {
  value = aws_db_instance.this.db_name
}

output "password" {
  value     = random_password.master.result
  sensitive = true
}
