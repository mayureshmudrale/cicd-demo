provider "kind" {}

# Each kind cluster gets its own aliased set of helm/kubernetes/kubectl
# providers, pointed at a fixed (not computed) kubeconfig path, so the
# provider configuration itself never depends on a resource attribute.
# module.cluster_* writes that file; everything else in that cluster's
# alias set must depend_on the cluster module to read it after it exists.

provider "helm" {
  alias = "cloud_a"
  kubernetes {
    config_path = local.kubeconfig_path_a
  }
}

provider "helm" {
  alias = "cloud_b"
  kubernetes {
    config_path = local.kubeconfig_path_b
  }
}

provider "kubernetes" {
  alias       = "cloud_a"
  config_path = local.kubeconfig_path_a
}

provider "kubernetes" {
  alias       = "cloud_b"
  config_path = local.kubeconfig_path_b
}

provider "kubectl" {
  alias            = "cloud_a"
  config_path      = local.kubeconfig_path_a
  load_config_file = true
}

provider "kubectl" {
  alias            = "cloud_b"
  config_path      = local.kubeconfig_path_b
  load_config_file = true
}
