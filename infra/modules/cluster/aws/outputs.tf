output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "kube_host" {
  value = aws_eks_cluster.this.endpoint
}

output "kube_ca" {
  value     = aws_eks_cluster.this.certificate_authority[0].data
  sensitive = true
}

output "kube_token" {
  value     = data.aws_eks_cluster_auth.this.token
  sensitive = true
}

# NLB-backed ingress-nginx, internal by default — matches this module's
# private-subnet-only cluster; flip to "internet-facing" at the chart
# level (never here) for a deployment that actually needs public ingress.
output "ingress_annotations" {
  value = {
    "service.beta.kubernetes.io/aws-load-balancer-type"   = "nlb"
    "service.beta.kubernetes.io/aws-load-balancer-scheme" = "internal"
  }
}

output "storage_class" {
  description = "Name only — creating the actual StorageClass resource is the platform module's job (it holds the kubernetes provider alias for this cluster), same division of responsibility as the local backend."
  value       = "gp3"
}
