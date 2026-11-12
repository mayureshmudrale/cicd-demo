variable "name" {
  description = "Database/cluster name"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large"
  type        = string
}

variable "network_id" {
  description = "Unused on the local backend; accepted for contract parity"
  type        = string
  default     = ""
}

variable "allowed_from" {
  description = "Unused on the local backend; CloudNativePG is reachable only in-cluster"
  type        = list(string)
  default     = []
}

variable "ha" {
  description = "Whether to run a 3-instance CNPG cluster instead of a single instance"
  type        = bool
  default     = false
}

variable "storage_size" {
  description = "PVC size per Postgres instance"
  type        = string
  default     = "2Gi"
}
