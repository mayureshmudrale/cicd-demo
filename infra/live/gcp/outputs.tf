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

# Same rationale as infra/live/aws's identical trio: lets CI build a
# kubeconfig from `terraform output` after apply, for `helm upgrade`.
output "kube_host" {
  value = module.cluster.kube_host
}

output "kube_ca" {
  value     = module.cluster.kube_ca
  sensitive = true
}

output "kube_token" {
  value     = module.cluster.kube_token
  sensitive = true
}
