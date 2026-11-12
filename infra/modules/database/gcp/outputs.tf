output "database_url" {
  value     = "postgresql+psycopg://${google_sql_user.this.name}:${random_password.master.result}@${google_sql_database_instance.this.private_ip_address}:5432/${google_sql_database.this.name}"
  sensitive = true
}

output "host" {
  value = google_sql_database_instance.this.private_ip_address
}

output "port" {
  value = 5432
}

# Same rationale as database/aws's identical trio: the live root needs
# these discrete fields to build an in-cluster secret shaped like CNPG's,
# since Cloud SQL has no operator writing one for it the way local does.
output "username" {
  value = google_sql_user.this.name
}

output "db_name" {
  value = google_sql_database.this.name
}

output "password" {
  value     = random_password.master.result
  sensitive = true
}
