variable "name" {
  description = "Logical network name (unused locally; kind manages its own docker network)"
  type        = string
}

variable "region" {
  description = "Unused on the local backend; accepted for contract parity"
  type        = string
  default     = ""
}

variable "cidr" {
  description = "Unused on the local backend; accepted for contract parity"
  type        = string
  default     = ""
}
