variable "tier_a" {
  description = "Size tier for cloud-a (the full-stack cluster)"
  type        = string
  default     = "small"
}

variable "tier_b" {
  description = "Size tier for cloud-b (the app-only cluster)"
  type        = string
  default     = "small"
}

variable "enable_cloud_b" {
  description = "Whether to stand up cloud-b at all. Set false to save RAM when you don't need to prove target-agnostic deploys."
  type        = bool
  default     = true
}

variable "gemini_api_key" {
  description = "Set via TF_VAR_gemini_api_key, never committed. Empty is a legitimate state: the AI evaluator falls back to its deterministic path."
  type        = string
  default     = ""
  sensitive   = true
}
