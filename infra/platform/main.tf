# Cloud-neutral platform layer. Nothing here branches on cloud — differences
# arrive only as variable values (service type, annotations) computed by the
# root from the cluster module's outputs.

resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.15.1"
  namespace        = "ingress-nginx"
  create_namespace = true
  wait             = true
  timeout          = 180

  set {
    name  = "controller.service.type"
    value = var.ingress_service_type
  }

  dynamic "set" {
    for_each = var.ingress_annotations
    content {
      name  = "controller.service.annotations.${replace(set.key, ".", "\\.")}"
      value = set.value
    }
  }
}

resource "helm_release" "argo_rollouts" {
  count = var.install_argo_rollouts ? 1 : 0

  name             = "argo-rollouts"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-rollouts"
  version          = "2.43.12"
  namespace        = "argo-rollouts"
  create_namespace = true
  wait             = true
  timeout          = 180
}

resource "kubernetes_namespace" "platform" {
  count = (var.install_otel_lgtm || var.install_ai_evaluator) ? 1 : 0

  metadata {
    name = "platform"
  }
}

# grafana/otel-lgtm: single-container Grafana+Loki+Tempo+Mimir+OTel-collector
# bundle, meant for exactly this kind of local/dev all-in-one observability
# backend. Not meant to scale or persist data past pod restarts.
resource "kubernetes_deployment" "otel_lgtm" {
  count = var.install_otel_lgtm ? 1 : 0

  metadata {
    name      = "otel-lgtm"
    namespace = kubernetes_namespace.platform[0].metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = { app = "otel-lgtm" }
    }

    template {
      metadata {
        labels = { app = "otel-lgtm" }
      }

      spec {
        container {
          name  = "otel-lgtm"
          image = var.otel_lgtm_image

          port { container_port = 3000 } # Grafana UI
          port { container_port = 4317 } # OTLP gRPC
          port { container_port = 4318 } # OTLP HTTP
          port { container_port = 3100 } # Loki
          port { container_port = 9090 } # Mimir/Prometheus-compatible

          resources {
            requests = { cpu = "250m", memory = "512Mi" }
            limits   = { cpu = "1", memory = "1Gi" }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "otel_lgtm" {
  count = var.install_otel_lgtm ? 1 : 0

  metadata {
    name      = "otel-lgtm"
    namespace = kubernetes_namespace.platform[0].metadata[0].name
  }

  spec {
    selector = { app = "otel-lgtm" }

    port {
      name        = "grafana"
      port        = 3000
      target_port = 3000
    }
    port {
      name        = "otlp-grpc"
      port        = 4317
      target_port = 4317
    }
    port {
      name        = "otlp-http"
      port        = 4318
      target_port = 4318
    }
    port {
      name        = "loki"
      port        = 3100
      target_port = 3100
    }
    port {
      name        = "mimir"
      port        = 9090
      target_port = 9090
    }
  }
}

# Feature #4 (adaptive canary routing), shadow mode by default: Argo's
# AnalysisTemplate (in deploy/helm/idea-board) calls this service mid-canary.
# Without a Gemini key it legitimately falls back to its deterministic
# "advance" path (ai.llm.GeminiUnavailable) rather than erroring.
resource "kubernetes_secret" "ai_evaluator" {
  count = var.install_ai_evaluator ? 1 : 0

  metadata {
    name      = "ai-evaluator"
    namespace = kubernetes_namespace.platform[0].metadata[0].name
  }

  data = {
    GEMINI_API_KEY = var.gemini_api_key
  }
}

resource "kubernetes_deployment" "ai_evaluator" {
  count = var.install_ai_evaluator ? 1 : 0

  metadata {
    name      = "ai-evaluator"
    namespace = kubernetes_namespace.platform[0].metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = { app = "ai-evaluator" }
    }

    template {
      metadata {
        labels = { app = "ai-evaluator" }
      }

      spec {
        container {
          name  = "ai-evaluator"
          image = var.ai_evaluator_image

          port { container_port = 8080 }

          env {
            name  = "AI_MODE_ROUTING"
            value = var.ai_mode_routing
          }
          env {
            name = "GEMINI_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.ai_evaluator[0].metadata[0].name
                key  = "GEMINI_API_KEY"
              }
            }
          }

          readiness_probe {
            http_get {
              path = "/healthz"
              port = 8080
            }
            initial_delay_seconds = 3
          }

          resources {
            requests = { cpu = "50m", memory = "128Mi" }
            limits   = { cpu = "250m", memory = "256Mi" }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "ai_evaluator" {
  count = var.install_ai_evaluator ? 1 : 0

  metadata {
    name      = "ai-evaluator"
    namespace = kubernetes_namespace.platform[0].metadata[0].name
  }

  spec {
    selector = { app = "ai-evaluator" }
    port {
      port        = 8080
      target_port = 8080
    }
  }
}
