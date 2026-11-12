variable "ingress_service_type" {
  description = "local: NodePort (no cloud LB controller). aws/gcp: LoadBalancer."
  type        = string
  default     = "LoadBalancer"
}

variable "ingress_annotations" {
  description = "Cloud-specific ingress-controller service annotations (from the cluster module's ingress_annotations output). Empty locally."
  type        = map(string)
  default     = {}
}

variable "install_argo_rollouts" {
  description = "Whether to install the Argo Rollouts controller. Skip on app-only clusters (e.g. cloud-b)."
  type        = bool
  default     = true
}

variable "install_otel_lgtm" {
  description = "Whether to install the otel-lgtm observability stack. Skip on app-only clusters (e.g. cloud-b)."
  type        = bool
  default     = true
}

variable "otel_lgtm_image" {
  type    = string
  default = "grafana/otel-lgtm:0.38.1"
}

variable "install_ai_evaluator" {
  description = "Whether to install the AI evaluator (feature #4, adaptive canary routing). Needs Argo Rollouts; meaningless without it."
  type        = bool
  default     = true
}

variable "ai_evaluator_image" {
  type    = string
  default = "ai-evaluator:local"
}

variable "ai_mode_routing" {
  description = "shadow: evaluator logs its verdict but always reports \"advance\" to Argo (never blocks). enforce: the real verdict gates the rollout."
  type        = string
  default     = "shadow"
}

variable "gemini_api_key" {
  description = "Optional. Without it the evaluator always falls back to its deterministic \"advance\" path (GeminiUnavailable), which is a legitimate state, not an error."
  type        = string
  default     = ""
  sensitive   = true
}
