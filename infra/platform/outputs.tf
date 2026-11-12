output "otel_lgtm_otlp_endpoint" {
  value = var.install_otel_lgtm ? "http://otel-lgtm.platform.svc.cluster.local:4317" : null
}
