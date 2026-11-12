variable "cloud" {
  description = "Target cloud backend: aws, gcp, or local"
  type        = string

  validation {
    condition     = contains(["aws", "gcp", "local"], var.cloud)
    error_message = "cloud must be one of: aws, gcp, local"
  }
}

variable "tier" {
  description = "Size tier: small, medium, or large"
  type        = string

  validation {
    condition     = contains(["small", "medium", "large"], var.tier)
    error_message = "tier must be one of: small, medium, large"
  }
}
