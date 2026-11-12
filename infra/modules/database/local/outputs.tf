output "database_url" {
  value     = data.kubernetes_secret.app_credentials.data["uri"]
  sensitive = true
}

output "host" {
  value = "${var.name}-rw.${kubernetes_namespace.db.metadata[0].name}.svc.cluster.local"
}

output "port" {
  value = 5432
}
