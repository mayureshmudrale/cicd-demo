resource "kind_cluster" "this" {
  name = var.name
  # Nodes can't reach Ready without a CNI, and Cilium (below) only installs
  # after this resource returns when install_cilium disables the default one.
  wait_for_ready  = var.install_cilium ? false : true
  kubeconfig_path = var.kubeconfig_path

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    networking {
      disable_default_cni = var.install_cilium
    }

    node {
      role = "control-plane"
    }

    dynamic "node" {
      for_each = range(var.node_count)
      content {
        role = "worker"
      }
    }
  }
}

resource "helm_release" "cilium" {
  count = var.install_cilium ? 1 : 0

  name       = "cilium"
  repository = "https://helm.cilium.io/"
  chart      = "cilium"
  namespace  = "kube-system"
  wait       = true

  set {
    name  = "hubble.relay.enabled"
    value = "true"
  }

  set {
    name  = "hubble.ui.enabled"
    value = "true"
  }

  depends_on = [kind_cluster.this]
}
