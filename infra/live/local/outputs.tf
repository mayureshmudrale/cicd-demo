output "cloud_a_cluster_name" {
  value = module.cluster_a.cluster_name
}

output "cloud_a_kubeconfig_path" {
  value = module.cluster_a.kubeconfig_path
}

output "cloud_a_storage_class" {
  value = module.cluster_a.storage_class
}

output "cloud_a_database_url" {
  value     = module.database_a.database_url
  sensitive = true
}

output "cloud_b_cluster_name" {
  value = var.enable_cloud_b ? module.cluster_b[0].cluster_name : null
}

output "cloud_b_kubeconfig_path" {
  value = var.enable_cloud_b ? module.cluster_b[0].kubeconfig_path : null
}
