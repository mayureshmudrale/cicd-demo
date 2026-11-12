output "cluster_name" {
  value = kind_cluster.this.name
}

output "kube_host" {
  value = kind_cluster.this.endpoint
}

output "kube_ca" {
  value     = kind_cluster.this.cluster_ca_certificate
  sensitive = true
}

# kind authenticates via client certificate, not a bearer token; kept for
# contract parity with the aws/gcp backends, which do return one.
output "kube_token" {
  value     = ""
  sensitive = true
}

output "ingress_annotations" {
  description = "OrbStack exposes kind's ingress-nginx NodePort/LoadBalancer directly to the Mac; no annotations needed"
  value       = {}
}

output "storage_class" {
  value = "standard"
}

output "kubeconfig_path" {
  value = kind_cluster.this.kubeconfig_path
}
