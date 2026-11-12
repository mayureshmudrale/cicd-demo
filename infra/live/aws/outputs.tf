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

# Exposed at the root (not just used internally by providers.tf) so CI can
# `terraform output` these to build a kubeconfig for `helm upgrade` after
# apply — the same short-lived token the kubernetes/helm providers use.
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
