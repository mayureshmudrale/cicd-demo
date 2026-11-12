resource "helm_release" "cnpg" {
  name             = "cnpg"
  repository       = "https://cloudnative-pg.github.io/charts"
  chart            = "cloudnative-pg"
  namespace        = "cnpg-system"
  create_namespace = true
  wait             = true
}

resource "kubernetes_namespace" "db" {
  metadata {
    name = var.name
  }
}

resource "kubectl_manifest" "postgres_cluster" {
  yaml_body = yamlencode({
    apiVersion = "postgresql.cnpg.io/v1"
    kind       = "Cluster"
    metadata = {
      name      = var.name
      namespace = kubernetes_namespace.db.metadata[0].name
    }
    spec = {
      instances = var.ha ? 3 : 1
      storage = {
        size = var.storage_size
      }
      bootstrap = {
        initdb = {
          database = "ideaboard"
          owner    = "ideaboard"
        }
      }
    }
  })

  depends_on = [helm_release.cnpg]
}

# CNPG writes the app user's credentials/URI to "<name>-app" only once it has
# reconciled the Cluster; give it a moment before reading the secret back.
resource "time_sleep" "wait_for_credentials" {
  depends_on      = [kubectl_manifest.postgres_cluster]
  create_duration = "60s"
}

data "kubernetes_secret" "app_credentials" {
  metadata {
    name      = "${var.name}-app"
    namespace = kubernetes_namespace.db.metadata[0].name
  }

  depends_on = [time_sleep.wait_for_credentials]
}
