output "cluster_name" {
  value = module.cluster.cluster_name
}

output "storage_class" {
  value = module.cluster.storage_class
}

output "ingress_annotations" {
  value = module.cluster.ingress_annotations
}

output "database_url" {
  value     = module.database.database_url
  sensitive = true
}

output "otel_lgtm_otlp_endpoint" {
  value = module.platform.otel_lgtm_otlp_endpoint
}
