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
