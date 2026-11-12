output "cluster_name" {
  value = google_container_cluster.this.name
}

output "kube_host" {
  value = "https://${google_container_cluster.this.endpoint}"
}

output "kube_ca" {
  value     = google_container_cluster.this.master_auth[0].cluster_ca_certificate
  sensitive = true
}

# Short-lived OAuth2 access token for the kubernetes/helm providers to
# auth with — same role as the AWS module's aws_eks_cluster_auth token,
# re-evaluated on every apply rather than stored.
output "kube_token" {
  value     = data.google_client_config.this.access_token
  sensitive = true
}

# GKE's external LoadBalancer handling needs no special annotations by
# default (unlike AWS' NLB type/scheme pair) — empty is the correct value
# here, not a placeholder.
output "ingress_annotations" {
  value = {}
}

output "storage_class" {
  description = "Name only — creating the actual StorageClass resource is the platform module's job, same division of responsibility as the local/aws backends."
  value       = "standard-rwo"
}
