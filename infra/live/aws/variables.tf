variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "tier" {
  description = "Size tier: small, medium, or large"
  type        = string
  default     = "small"
}

variable "gemini_api_key" {
  description = "Set via TF_VAR_gemini_api_key, never committed. Empty is a legitimate state: the AI evaluator falls back to its deterministic path."
  type        = string
  default     = ""
  sensitive   = true
}

variable "ai_evaluator_image" {
  description = "A real ECR URI, e.g. <account>.dkr.ecr.<region>.amazonaws.com/ai-evaluator:<tag> — the local backend's own default (\"ai-evaluator:local\") only resolves inside a kind node's image cache, not here."
  type        = string
  default     = "ai-evaluator:local"
}
