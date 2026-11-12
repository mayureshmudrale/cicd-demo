locals {
  kubeconfig_path_a = "${path.module}/.kubeconfig-cloud-a"
  kubeconfig_path_b = "${path.module}/.kubeconfig-cloud-b"
}

# --- cloud-a: full stack (this module wires network -> cluster -> database;
# ingress-nginx, Argo Rollouts, otel-lgtm, toxiproxy and the AI evaluator are
# cloud-neutral Helm releases added in infra/platform, phase 2) ---

module "tiers_a" {
  source = "../../modules/tiers"
  cloud  = "local"
  tier   = var.tier_a
}

module "network_a" {
  source = "../../modules/network/local"
  name   = "cloud-a"
}

module "cluster_a" {
  source = "../../modules/cluster/local"

  name            = "cloud-a"
  tier            = var.tier_a
  network_id      = module.network_a.network_id
  node_count      = module.tiers_a.node_count - 1
  kubeconfig_path = local.kubeconfig_path_a

  providers = {
    helm = helm.cloud_a
  }
}

module "database_a" {
  source = "../../modules/database/local"

  name       = "ideaboard"
  tier       = var.tier_a
  network_id = module.network_a.network_id
  ha         = module.tiers_a.db_ha

  providers = {
    helm       = helm.cloud_a
    kubernetes = kubernetes.cloud_a
    kubectl    = kubectl.cloud_a
  }

  depends_on = [module.cluster_a]
}

module "platform_a" {
  source = "../../platform"

  # kind has no cloud load balancer controller; NodePort is the local
  # equivalent of what aws/gcp express via LoadBalancer + ingress_annotations.
  ingress_service_type = "NodePort"
  ingress_annotations  = module.cluster_a.ingress_annotations
  gemini_api_key       = var.gemini_api_key

  providers = {
    helm       = helm.cloud_a
    kubernetes = kubernetes.cloud_a
  }

  depends_on = [module.cluster_a]
}

# --- cloud-b: app-only, deployed by the same chart to prove the pipeline is
# target-agnostic. Tear down (set enable_cloud_b = false) when not in use. ---

module "tiers_b" {
  count  = var.enable_cloud_b ? 1 : 0
  source = "../../modules/tiers"
  cloud  = "local"
  tier   = var.tier_b
}

module "network_b" {
  count  = var.enable_cloud_b ? 1 : 0
  source = "../../modules/network/local"
  name   = "cloud-b"
}

module "cluster_b" {
  count  = var.enable_cloud_b ? 1 : 0
  source = "../../modules/cluster/local"

  name            = "cloud-b"
  tier            = var.tier_b
  network_id      = module.network_b[0].network_id
  node_count      = module.tiers_b[0].node_count - 1
  kubeconfig_path = local.kubeconfig_path_b

  providers = {
    helm = helm.cloud_b
  }
}

module "database_b" {
  count  = var.enable_cloud_b ? 1 : 0
  source = "../../modules/database/local"

  name       = "ideaboard"
  tier       = var.tier_b
  network_id = module.network_b[0].network_id
  ha         = module.tiers_b[0].db_ha

  providers = {
    helm       = helm.cloud_b
    kubernetes = kubernetes.cloud_b
    kubectl    = kubectl.cloud_b
  }

  depends_on = [module.cluster_b]
}

module "platform_b" {
  count  = var.enable_cloud_b ? 1 : 0
  source = "../../platform"

  ingress_service_type  = "NodePort"
  ingress_annotations   = module.cluster_b[0].ingress_annotations
  install_argo_rollouts = false # app-only cluster: proves the chart deploys, not canaries
  install_otel_lgtm     = false
  install_ai_evaluator  = false

  providers = {
    helm       = helm.cloud_b
    kubernetes = kubernetes.cloud_b
  }

  depends_on = [module.cluster_b]
}
